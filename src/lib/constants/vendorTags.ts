/**
 * LLM 厂商预制标签系统
 * 根据不同的模型厂商提供推荐的标签
 */

export const VENDOR_TAGS = {
	// OpenAI 系列模型标签
	openai: {
		vendor: 'OpenAI',
		tags: [
			{ name: 'gpt', category: 'model-family', description: 'GPT 系列模型' },
			{ name: 'chatgpt', category: 'product', description: 'ChatGPT 产品' },
			{ name: 'api', category: 'access', description: 'API 访问' },
			{ name: 'cloud', category: 'deployment', description: '云端部署' },
			{ name: 'multimodal', category: 'capability', description: '多模态能力' },
			{ name: 'reasoning', category: 'capability', description: '推理能力' },
			{ name: 'coding', category: 'use-case', description: '编程助手' },
			{ name: 'writing', category: 'use-case', description: '写作助手' },
			{ name: 'analysis', category: 'use-case', description: '分析工具' },
			{ name: 'english', category: 'language', description: '英语优化' },
			{ name: 'premium', category: 'tier', description: '高级服务' },
			{ name: 'fast', category: 'performance', description: '快速响应' }
		],
		modelSpecific: {
			'gpt-4': ['gpt-4', 'advanced', 'reasoning', 'multimodal'],
			'gpt-4-turbo': ['gpt-4', 'turbo', 'fast', 'multimodal'],
			'gpt-3.5-turbo': ['gpt-3.5', 'turbo', 'fast', 'efficient'],
			'dall-e': ['image-generation', 'creative', 'visual'],
			'whisper': ['speech-to-text', 'audio', 'transcription']
		}
	},

	// Ollama 本地模型标签
	ollama: {
		vendor: 'Ollama',
		tags: [
			{ name: 'local', category: 'deployment', description: '本地部署' },
			{ name: 'open-source', category: 'license', description: '开源模型' },
			{ name: 'privacy', category: 'feature', description: '隐私保护' },
			{ name: 'offline', category: 'access', description: '离线使用' },
			{ name: 'customizable', category: 'feature', description: '可定制' },
			{ name: 'free', category: 'cost', description: '免费使用' },
			{ name: 'llama', category: 'model-family', description: 'LLaMA 系列' },
			{ name: 'mistral', category: 'model-family', description: 'Mistral 系列' },
			{ name: 'qwen', category: 'model-family', description: '通义千问系列' },
			{ name: 'chat', category: 'type', description: '对话模型' },
			{ name: 'coding', category: 'use-case', description: '代码生成' },
			{ name: 'reasoning', category: 'capability', description: '推理能力' }
		],
		modelSpecific: {
			'llama': ['llama', 'meta', 'open-source', 'reasoning'],
			'llama2': ['llama2', 'meta', 'open-source', 'improved'],
			'llama3': ['llama3', 'meta', 'open-source', 'advanced'],
			'mistral': ['mistral', 'open-source', 'fast', 'efficient'],
			'codellama': ['codellama', 'coding', 'llama', 'specialized'],
			'qwen': ['qwen', 'alibaba', 'chinese', 'multilingual'],
			'gemma': ['gemma', 'google', 'open-source', 'lightweight'],
			'phi': ['phi', 'microsoft', 'small', 'efficient']
		}
	},

	// Anthropic Claude 系列
	anthropic: {
		vendor: 'Anthropic',
		tags: [
			{ name: 'claude', category: 'model-family', description: 'Claude 系列' },
			{ name: 'constitutional-ai', category: 'approach', description: '宪法 AI' },
			{ name: 'safety', category: 'feature', description: '安全优先' },
			{ name: 'helpful', category: 'trait', description: '乐于助人' },
			{ name: 'harmless', category: 'trait', description: '无害设计' },
			{ name: 'honest', category: 'trait', description: '诚实可靠' },
			{ name: 'reasoning', category: 'capability', description: '推理能力' },
			{ name: 'analysis', category: 'use-case', description: '分析任务' },
			{ name: 'writing', category: 'use-case', description: '写作辅助' },
			{ name: 'research', category: 'use-case', description: '研究助手' }
		],
		modelSpecific: {
			'claude-3': ['claude-3', 'opus', 'sonnet', 'haiku'],
			'claude-2': ['claude-2', 'legacy', 'capable']
		}
	},

	// DeepSeek 系列模型
	deepseek: {
		vendor: 'DeepSeek',
		tags: [
			{ name: 'deepseek', category: 'model-family', description: 'DeepSeek 系列' },
			{ name: 'chinese', category: 'language', description: '中文优化' },
			{ name: 'bilingual', category: 'language', description: '双语能力' },
			{ name: 'coding', category: 'use-case', description: '编程助手' },
			{ name: 'math', category: 'specialty', description: '数学推理' },
			{ name: 'reasoning', category: 'capability', description: '推理能力' },
			{ name: 'cost-effective', category: 'cost', description: '成本效益高' },
			{ name: 'api', category: 'access', description: 'API 访问' },
			{ name: 'fast', category: 'performance', description: '快速响应' },
			{ name: 'efficient', category: 'performance', description: '高效运行' },
			{ name: 'opensource', category: 'license', description: '开源模型' },
			{ name: 'enterprise', category: 'use-case', description: '企业应用' }
		],
		modelSpecific: {
			'deepseek-coder': ['deepseek-coder', 'coding', 'specialized', 'efficient'],
			'deepseek-chat': ['deepseek-chat', 'conversation', 'chinese', 'bilingual'],
			'deepseek-v2': ['deepseek-v2', 'advanced', 'reasoning', 'math'],
			'deepseek-v3': ['deepseek-v3', 'latest', 'improved', 'multimodal']
		}
	},

	// 通义千问系列模型 (Qwen)
	qwen: {
		vendor: 'Alibaba',
		tags: [
			{ name: 'qwen', category: 'model-family', description: '通义千问系列' },
			{ name: 'alibaba', category: 'vendor', description: '阿里巴巴出品' },
			{ name: 'chinese', category: 'language', description: '中文优化' },
			{ name: 'multilingual', category: 'language', description: '多语言支持' },
			{ name: 'coding', category: 'use-case', description: '编程助手' },
			{ name: 'math', category: 'specialty', description: '数学能力' },
			{ name: 'reasoning', category: 'capability', description: '推理能力' },
			{ name: 'knowledge', category: 'capability', description: '知识丰富' },
			{ name: 'enterprise', category: 'use-case', description: '企业应用' },
			{ name: 'opensource', category: 'license', description: '开源模型' },
			{ name: 'api', category: 'access', description: 'API 访问' },
			{ name: 'versatile', category: 'trait', description: '多才多艺' }
		],
		modelSpecific: {
			'qwen-turbo': ['qwen-turbo', 'fast', 'efficient', 'cost-effective'],
			'qwen-plus': ['qwen-plus', 'balanced', 'reliable', 'enterprise'],
			'qwen-max': ['qwen-max', 'powerful', 'advanced', 'premium'],
			'qwen-coder': ['qwen-coder', 'coding', 'specialized', 'technical'],
			'qwen-vl': ['qwen-vl', 'vision', 'multimodal', 'visual'],
			'qwen-audio': ['qwen-audio', 'audio', 'speech', 'multimodal']
		}
	},

	// Google Gemini 系列 (扩展)
	google: {
		vendor: 'Google',
		tags: [
			{ name: 'gemini', category: 'model-family', description: 'Gemini 系列' },
			{ name: 'google', category: 'vendor', description: 'Google 出品' },
			{ name: 'multimodal', category: 'capability', description: '多模态能力' },
			{ name: 'native-multimodal', category: 'feature', description: '原生多模态' },
			{ name: 'vision', category: 'capability', description: '视觉理解' },
			{ name: 'audio', category: 'capability', description: '音频处理' },
			{ name: 'video', category: 'capability', description: '视频理解' },
			{ name: 'reasoning', category: 'capability', description: '推理能力' },
			{ name: 'coding', category: 'use-case', description: '编程助手' },
			{ name: 'math', category: 'specialty', description: '数学能力' },
			{ name: 'research', category: 'use-case', description: '研究工具' },
			{ name: 'api', category: 'access', description: 'API 访问' },
			{ name: 'cloud', category: 'deployment', description: '云端部署' },
			{ name: 'enterprise', category: 'use-case', description: '企业应用' },
			{ name: 'fast', category: 'performance', description: '快速响应' }
		],
		modelSpecific: {
			'gemini-pro': ['gemini-pro', 'advanced', 'multimodal', 'powerful'],
			'gemini-pro-vision': ['gemini-pro-vision', 'vision', 'visual', 'image-understanding'],
			'gemini-1.5-pro': ['gemini-1.5-pro', 'latest', 'improved', 'context-window'],
			'gemini-1.5-flash': ['gemini-1.5-flash', 'fast', 'efficient', 'cost-effective'],
			'gemini-ultra': ['gemini-ultra', 'premium', 'most-capable', 'advanced'],
			'palm': ['palm', 'legacy', 'text-generation', 'foundation']
		}
	},

	// GLM (智谱 AI) 系列模型
	glm: {
		vendor: 'ZhipuAI',
		tags: [
			{ name: 'glm', category: 'model-family', description: 'GLM 系列' },
			{ name: 'zhipuai', category: 'vendor', description: '智谱 AI 出品' },
			{ name: 'chinese', category: 'language', description: '中文优化' },
			{ name: 'bilingual', category: 'language', description: '双语能力' },
			{ name: 'multilingual', category: 'language', description: '多语言支持' },
			{ name: 'coding', category: 'use-case', description: '编程助手' },
			{ name: 'reasoning', category: 'capability', description: '推理能力' },
			{ name: 'knowledge', category: 'capability', description: '知识丰富' },
			{ name: 'academic', category: 'use-case', description: '学术研究' },
			{ name: 'opensource', category: 'license', description: '开源模型' },
			{ name: 'api', category: 'access', description: 'API 访问' },
			{ name: 'efficient', category: 'performance', description: '高效运行' },
			{ name: 'versatile', category: 'trait', description: '多才多艺' }
		],
		modelSpecific: {
			'glm-4': ['glm-4', 'latest', 'improved', 'advanced'],
			'glm-3-turbo': ['glm-3-turbo', 'fast', 'efficient', 'turbo'],
			'glm-130b': ['glm-130b', 'large', 'powerful', 'bilingual'],
			'glm-6b': ['glm-6b', 'opensource', 'efficient', 'lightweight'],
			'chatglm': ['chatglm', 'conversation', 'chinese', 'dialogue'],
			'chatglm3': ['chatglm3', 'improved', 'conversation', 'knowledge'],
			'codegeex': ['codegeex', 'coding', 'specialized', 'technical']
		}
	},

	// 其他通用标签
	general: {
		vendor: 'General',
		tags: [
			// 能力类标签
			{ name: 'text-generation', category: 'capability', description: '文本生成' },
			{ name: 'conversation', category: 'use-case', description: '对话聊天' },
			{ name: 'qa', category: 'use-case', description: '问答系统' },
			{ name: 'summarization', category: 'use-case', description: '文本摘要' },
			{ name: 'translation', category: 'use-case', description: '语言翻译' },
			{ name: 'creative', category: 'trait', description: '创意写作' },
			{ name: 'logical', category: 'trait', description: '逻辑推理' },

			// 技术类标签
			{ name: 'transformer', category: 'architecture', description: 'Transformer 架构' },
			{ name: 'attention', category: 'mechanism', description: '注意力机制' },
			{ name: 'pretrained', category: 'training', description: '预训练模型' },
			{ name: 'finetuned', category: 'training', description: '微调模型' },

			// 规模类标签
			{ name: 'small', category: 'size', description: '小型模型' },
			{ name: 'medium', category: 'size', description: '中型模型' },
			{ name: 'large', category: 'size', description: '大型模型' },
			{ name: 'xl', category: 'size', description: '超大型模型' },

			// 性能类标签
			{ name: 'fast', category: 'performance', description: '快速响应' },
			{ name: 'efficient', category: 'performance', description: '高效运行' },
			{ name: 'lightweight', category: 'performance', description: '轻量级' },
			{ name: 'resource-intensive', category: 'performance', description: '资源密集' },

			// 用途类标签
			{ name: 'general-purpose', category: 'use-case', description: '通用目的' },
			{ name: 'specialized', category: 'use-case', description: '专门用途' },
			{ name: 'educational', category: 'use-case', description: '教育用途' },
			{ name: 'professional', category: 'use-case', description: '专业用途' },

			// 语言类标签
			{ name: 'multilingual', category: 'language', description: '多语言支持' },
			{ name: 'chinese', category: 'language', description: '中文优化' },
			{ name: 'english', category: 'language', description: '英语优化' },
			{ name: 'code', category: 'language', description: '代码语言' }
		]
	}
};

/**
 * 根据模型信息获取推荐的标签
 */
export function getRecommendedTags(modelInfo: {
	owned_by?: string;
	name?: string;
	id?: string;
	base_model_id?: string;
}): Array<{ name: string; category: string; description: string }> {
	const recommendations: Array<{ name: string; category: string; description: string }> = [];

	if (!modelInfo) return recommendations;

	// 获取基础厂商标签
	const vendor = modelInfo.owned_by || modelInfo.base_model_id?.split(':')[0];
	if (vendor && VENDOR_TAGS[vendor as keyof typeof VENDOR_TAGS]) {
		recommendations.push(...VENDOR_TAGS[vendor as keyof typeof VENDOR_TAGS].tags);
	}

	// 添加通用标签
	recommendations.push(...VENDOR_TAGS.general.tags);

	// 根据模型名称添加特定标签
	const modelName = modelInfo.name || modelInfo.id || '';

	Object.entries(VENDOR_TAGS).forEach(([vendorKey, vendorData]) => {
		if (vendorData.modelSpecific) {
			Object.entries(vendorData.modelSpecific).forEach(([modelPattern, modelTags]) => {
				if (modelName.toLowerCase().includes(modelPattern.toLowerCase())) {
					// 将模型特定标签转换为推荐格式
					modelTags.forEach(tagName => {
						const tag = vendorData.tags.find(t => t.name === tagName);
						if (tag) {
							recommendations.push(tag);
						} else {
							// 如果没有找到预定义标签，创建一个基础标签
							recommendations.push({
								name: tagName,
								category: 'model-specific',
								description: `${modelPattern}特定标签`
							});
						}
					});
				}
			});
		}
	});

	// 去重并返回
	return recommendations.filter((tag, index, self) =>
		index === self.findIndex(t => t.name === tag.name)
	);
}

/**
 * 根据输入过滤标签建议
 */
export function filterTagSuggestions(
	input: string,
	modelInfo: { owned_by?: string; name?: string; id?: string; base_model_id?: string }
): Array<{ value: string; label: string; category?: string; description?: string }> {
	const recommendedTags = getRecommendedTags(modelInfo);
	const inputLower = input.toLowerCase();

	const filtered = recommendedTags
		.filter(tag => tag.name.toLowerCase().includes(inputLower))
		.slice(0, 8) // 限制建议数量
		.map(tag => ({
			value: tag.name,
			label: `${tag.name}${tag.category ? ` (${tag.category})` : ''}`,
			category: tag.category,
			description: tag.description
		}));

	// 如果输入不为空且不在推荐标签中，添加新建选项
	if (input.trim() && !filtered.some(item => item.value.toLowerCase() === inputLower)) {
		filtered.unshift({
			value: input.trim(),
			label: `${input.trim()} (新建)`,
			category: 'custom',
			description: '自定义标签'
		});
	}

	return filtered;
}