export type Banner = {
	id: string;
	type: string;
	title?: string;
	content: string;
	url?: string;
	dismissible?: boolean;
	timestamp: number;
};

export enum TTS_RESPONSE_SPLIT {
	PUNCTUATION = 'punctuation',
	PARAGRAPHS = 'paragraphs',
	NONE = 'none'
}

export type ToolServer = {
	url: string;
	key?: string;
	auth_type?: string;
	openapi: any;
	info: any;
	specs: {
		type: string;
		name: any;
		description: any;
		parameters: {
			type: string;
			properties: object;
			required: never[];
		};
	}[];
};

export interface DocInfo {
	id: string;
	url: string;
	title: string;
	isLoading?: boolean;
}
