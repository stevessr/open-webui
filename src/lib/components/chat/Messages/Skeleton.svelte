<script lang="ts">
	export let size = 'md';
</script>

<span class="relative flex {size === 'md' ? 'size-3 my-2' : 'size-2 my-1'} mx-1">
	<span
		class="absolute inline-flex h-full w-full breathing-light-skeleton rounded-full opacity-75"
	></span>
	<span
		class="relative inline-flex {size === 'md'
			? 'size-3'
			: 'size-2'} rounded-full breathing-light-core"
	></span>
</span>

<style>
	.breathing-light-skeleton {
		background: linear-gradient(45deg, #374151, #6b7280, #9ca3af, #d1d5db);
		background-size: 400% 400%;
		animation: breathe-skeleton 2s ease-in-out infinite;
	}

	.breathing-light-core {
		background: linear-gradient(45deg, #000000, #374151, #6b7280, #ffffff);
		background-size: 400% 400%;
		animation: breathe-core 2s ease-in-out infinite;
	}

	@keyframes breathe-skeleton {
		0% {
			opacity: 0.3;
			transform: scale(0.9);
			background-position: 0% 50%;
		}
		25% {
			opacity: 0.6;
			transform: scale(1.0);
			background-position: 100% 50%;
		}
		50% {
			opacity: 0.8;
			transform: scale(1.1);
			background-position: 50% 100%;
		}
		75% {
			opacity: 0.6;
			transform: scale(1.0);
			background-position: 0% 100%;
		}
		100% {
			opacity: 0.3;
			transform: scale(0.9);
			background-position: 0% 50%;
		}
	}

	@keyframes breathe-core {
		0% {
			opacity: 0.5;
			transform: scale(0.8);
			background-position: 0% 50%;
		}
		25% {
			opacity: 0.8;
			transform: scale(1.0);
			background-position: 100% 50%;
		}
		50% {
			opacity: 1.0;
			transform: scale(1.25);
			background-position: 50% 100%;
		}
		75% {
			opacity: 0.8;
			transform: scale(1.0);
			background-position: 0% 100%;
		}
		100% {
			opacity: 0.5;
			transform: scale(0.8);
			background-position: 0% 50%;
		}
	}

	/* Dark mode adjustments */
	:global(.dark) .breathing-light-skeleton {
		background: linear-gradient(45deg, #d1d5db, #9ca3af, #6b7280, #374151);
	}

	:global(.dark) .breathing-light-core {
		background: linear-gradient(45deg, #ffffff, #d1d5db, #9ca3af, #000000);
	}
</style>
