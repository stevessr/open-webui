<script lang="ts">
	export let className: string = 'size-4';
	export let colorful: boolean = true;
</script>

<div class="flex justify-center text-center">
	<div
		class="breathing-light-spinner {className}"
		class:colorful
		aria-hidden="true"
	>
		<style>
			.breathing-light-spinner {
				border-radius: 50%;
				background: linear-gradient(45deg, #3b82f6, #8b5cf6, #06b6d4, #10b981);
				background-size: 400% 400%;
				animation: breathe-spinner 2s ease-in-out infinite;
			}

			.breathing-light-spinner.colorful {
				animation: breathe-spinner-colorful 2s ease-in-out infinite, spinner-gradient 3s infinite ease-in-out;
			}

			@keyframes breathe-spinner {
				0% {
					opacity: 0.4;
					transform: scale(0.8);
					box-shadow: 0 0 5px rgba(59, 130, 246, 0.3);
				}
				25% {
					opacity: 0.7;
					transform: scale(1.0);
					box-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
				}
				50% {
					opacity: 1;
					transform: scale(1.2);
					box-shadow: 0 0 15px rgba(6, 182, 212, 0.7);
				}
				75% {
					opacity: 0.7;
					transform: scale(1.0);
					box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
				}
				100% {
					opacity: 0.4;
					transform: scale(0.8);
					box-shadow: 0 0 5px rgba(59, 130, 246, 0.3);
				}
			}

			@keyframes breathe-spinner-colorful {
				0% {
					opacity: 0.5;
					transform: scale(0.9);
					box-shadow: 0 0 8px rgba(59, 130, 246, 0.4);
				}
				25% {
					opacity: 0.8;
					transform: scale(1.1);
					box-shadow: 0 0 12px rgba(139, 92, 246, 0.6);
				}
				50% {
					opacity: 1;
					transform: scale(1.3);
					box-shadow: 0 0 20px rgba(6, 182, 212, 0.8);
				}
				75% {
					opacity: 0.8;
					transform: scale(1.1);
					box-shadow: 0 0 12px rgba(16, 185, 129, 0.6);
				}
				100% {
					opacity: 0.5;
					transform: scale(0.9);
					box-shadow: 0 0 8px rgba(59, 130, 246, 0.4);
				}
			}

			@keyframes spinner-gradient {
				0%, 100% {
					background-position: 0% 50%;
					filter: hue-rotate(0deg) saturate(1.2) brightness(1.1);
				}
				25% {
					background-position: 100% 50%;
					filter: hue-rotate(90deg) saturate(1.4) brightness(1.2);
				}
				50% {
					background-position: 50% 100%;
					filter: hue-rotate(180deg) saturate(1.6) brightness(1.3);
				}
				75% {
					background-position: 0% 100%;
					filter: hue-rotate(270deg) saturate(1.4) brightness(1.2);
				}
			}

			/* Dark mode adjustments */
			:global(.dark) .breathing-light-spinner {
				background: linear-gradient(45deg, #1e40af, #7c3aed, #0891b2, #059669);
				box-shadow: 0 0 10px rgba(139, 92, 246, 0.6);
			}
		</style>
	</div>
</div>
