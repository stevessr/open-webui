import { EventSourceParserStream } from 'eventsource-parser/stream';
import type { ParsedEvent } from 'eventsource-parser';

type TextStreamUpdate = {
	done: boolean;
	value: string;
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	sources?: any;
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	selectedModelId?: any;
	error?: any;
	usage?: ResponseUsage;
};

type ResponseUsage = {
	/** Including images and tools if any */
	prompt_tokens: number;
	/** The tokens generated */
	completion_tokens: number;
	/** Sum of the above two fields */
	total_tokens: number;
	/** Any other fields that aren't part of the base OpenAI spec */
	[other: string]: unknown;
};

// createOpenAITextStream takes a responseBody with a SSE response,
// and returns an async generator that emits delta updates with large deltas chunked into random sized chunks
export async function createOpenAITextStream(
	responseBody: ReadableStream<Uint8Array>,
	splitLargeDeltas: boolean,
	type: string = 'openai'
): Promise<AsyncGenerator<TextStreamUpdate>> {
	const eventStream = responseBody
		.pipeThrough(new TextDecoderStream())
		.pipeThrough(new EventSourceParserStream())
		.getReader();
	let iterator = streamToIterator(eventStream, type);
	if (splitLargeDeltas) {
		iterator = streamLargeDeltasAsRandomChunks(iterator);
	}
	return iterator;
}

const parseAnthropicDelta = (parsedData: any): TextStreamUpdate | null => {
	if (parsedData.type === 'content_block_delta') {
		const content = parsedData.delta?.text ?? '';
		return { done: false, value: content };
	}

	if (parsedData.type === 'message_start') {
		if (parsedData.message?.usage) {
			return {
				done: false,
				value: '',
				usage: {
					prompt_tokens: parsedData.message.usage.input_tokens,
					completion_tokens: parsedData.message.usage.output_tokens,
					total_tokens:
						parsedData.message.usage.input_tokens + parsedData.message.usage.output_tokens
				}
			};
		}
	}

	if (parsedData.type === 'message_delta') {
		if (parsedData.usage) {
			return {
				done: false,
				value: '',
				usage: {
					prompt_tokens: 0,
					completion_tokens: parsedData.usage.output_tokens,
					total_tokens: parsedData.usage.output_tokens
				}
			};
		}
	}

	return null;
};

const parseGeminiDelta = (parsedData: any): TextStreamUpdate | null => {
	if (parsedData.candidates) {
		const content = parsedData.candidates?.[0]?.content?.parts?.[0]?.text ?? '';
		return { done: false, value: content };
	}
	return null;
};

const parseResponseAPIDelta = (parsedData: any): TextStreamUpdate | null => {
	if (parsedData.type === 'response.output_text.delta') {
		return { done: false, value: parsedData.delta };
	}
	return null;
};

const parseOpenAIDelta = (parsedData: any): TextStreamUpdate | null => {
	if (parsedData.choices?.[0]?.delta?.content) {
		return {
			done: false,
			value: parsedData.choices?.[0]?.delta?.content ?? ''
		};
	}
	// Fallback for other OpenAI fields or empty content
	if (parsedData.choices?.[0]?.finish_reason) {
		// Sometimes finish_reason comes with empty content
		return { done: false, value: '' };
	}

	// If we have choices but no delta content (maybe empty delta), return empty
	if (parsedData.choices && parsedData.choices.length > 0) {
		return { done: false, value: '' };
	}

	return null;
};

async function* streamToIterator(
	reader: ReadableStreamDefaultReader<ParsedEvent>,
	type: string = 'openai'
): AsyncGenerator<TextStreamUpdate> {
	while (true) {
		const { value, done } = await reader.read();
		if (done) {
			yield { done: true, value: '' };
			break;
		}
		if (!value) {
			continue;
		}
		const data = value.data;
		if (data.startsWith('[DONE]')) {
			yield { done: true, value: '' };
			break;
		}

		try {
			let dataToParse = data;
			// Handle potential double data: prefix or parser issues
			if (dataToParse.startsWith('data: ')) {
				dataToParse = dataToParse.slice(6);
			}

			const parsedData = JSON.parse(dataToParse);
			console.log(parsedData);

			if (parsedData.error) {
				yield { done: true, value: '', error: parsedData.error };
				break;
			}

			if (parsedData.sources) {
				yield { done: false, value: '', sources: parsedData.sources };
				continue;
			}

			if (parsedData.selected_model_id) {
				yield { done: false, value: '', selectedModelId: parsedData.selected_model_id };
				continue;
			}

			if (parsedData.usage) {
				yield { done: false, value: '', usage: parsedData.usage };
				continue;
			}

			if (parsedData.usageMetadata) {
				yield {
					done: false,
					value: '',
					usage: {
						prompt_tokens: parsedData.usageMetadata.promptTokenCount,
						completion_tokens: parsedData.usageMetadata.candidatesTokenCount,
						total_tokens: parsedData.usageMetadata.totalTokenCount
					}
				};
				continue;
			}

			let update = null;
			switch (type) {
				case 'anthropic':
					update = parseAnthropicDelta(parsedData);
					break;
				case 'gemini':
					update = parseGeminiDelta(parsedData);
					break;
				case 'responses':
					update = parseResponseAPIDelta(parsedData);
					break;
				default:
					// openai
					update = parseOpenAIDelta(parsedData);
			}
			if (update) {
				yield update;
				continue;
			}

			// If no specific parser matched but we have a valid object,
			// and it didn't match common fields, we might just yield empty or ignore.
			// Assuming if it was a text delta it would be caught by parseOpenAIDelta.
		} catch (e) {
			console.error('Error extracting delta from SSE event:', e);
		}
	}
}

// streamLargeDeltasAsRandomChunks will chunk large deltas (length > 5) into random sized chunks between 1-3 characters
// This is to simulate a more fluid streaming, even though some providers may send large chunks of text at once
async function* streamLargeDeltasAsRandomChunks(
	iterator: AsyncGenerator<TextStreamUpdate>
): AsyncGenerator<TextStreamUpdate> {
	for await (const textStreamUpdate of iterator) {
		if (textStreamUpdate.done) {
			yield textStreamUpdate;
			return;
		}

		if (textStreamUpdate.error) {
			yield textStreamUpdate;
			continue;
		}
		if (textStreamUpdate.sources) {
			yield textStreamUpdate;
			continue;
		}
		if (textStreamUpdate.selectedModelId) {
			yield textStreamUpdate;
			continue;
		}
		if (textStreamUpdate.usage) {
			yield textStreamUpdate;
			continue;
		}

		let content = textStreamUpdate.value;
		if (content.length < 5) {
			yield { done: false, value: content };
			continue;
		}
		while (content != '') {
			const chunkSize = Math.min(Math.floor(Math.random() * 3) + 1, content.length);
			const chunk = content.slice(0, chunkSize);
			yield { done: false, value: chunk };
			// Do not sleep if the tab is hidden
			// Timers are throttled to 1s in hidden tabs
			if (document?.visibilityState !== 'hidden') {
				await sleep(5);
			}
			content = content.slice(chunkSize);
		}
	}
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
