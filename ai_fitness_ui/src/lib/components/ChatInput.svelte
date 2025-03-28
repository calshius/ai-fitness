<script>
    import { createEventDispatcher } from 'svelte';
    import { chatStore } from '$lib/stores/chatStore';
    
    const dispatch = createEventDispatcher();
    
    let query = '';
    let inputHeight = 56; // Default height
    let textarea;
    
    function handleSubmit() {
        if (query.trim() && !$chatStore.isLoading) {
            dispatch('submit', query);
            query = '';
            // Reset textarea height
            if (textarea) {
                textarea.style.height = '56px';
                inputHeight = 56;
            }
        }
    }
    
    function handleKeydown(event) {
        // Submit on Enter (without Shift)
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleSubmit();
        }
    }
    
    function autoResize() {
        if (textarea) {
            // Reset height to auto to get the correct scrollHeight
            textarea.style.height = 'auto';
            // Set new height based on scrollHeight (with min height of 56px)
            const newHeight = Math.max(56, textarea.scrollHeight);
            textarea.style.height = `${newHeight}px`;
            inputHeight = newHeight;
        }
    }
</script>

<div class="input-container" style="--input-height: {inputHeight}px">
    <textarea
        bind:this={textarea}
        bind:value={query}
        on:keydown={handleKeydown}
        on:input={autoResize}
        placeholder="Ask about your fitness data..."
        disabled={$chatStore.isLoading}
        rows="1"
    ></textarea>
    <button 
        on:click={handleSubmit} 
        disabled={!query.trim() || $chatStore.isLoading}
        class:loading={$chatStore.isLoading}
    >
        {#if $chatStore.isLoading}
            <div class="spinner"></div>
        {:else}
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
        {/if}
    </button>
</div>

<style>
    .input-container {
        display: flex;
        align-items: center;
        background-color: white;
        border-radius: 1.5rem;
        padding: 0.75rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        margin: 1rem 0;
        position: relative;
    }

    textarea {
        flex: 1;
        border: none;
        outline: none;
        resize: none;
        padding: 0.5rem 1rem;
        font-size: 1rem;
        font-family: inherit;
        height: var(--input-height);
        max-height: 200px;
        overflow-y: auto;
    }

    button {
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s;
    }

    button:hover:not(:disabled) {
        background-color: #2563eb;
    }

    button:disabled {
        background-color: #93c5fd;
        cursor: not-allowed;
    }

    .loading {
        position: relative;
    }

    .spinner {
        width: 20px;
        height: 20px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: white;
        animation: spin 1s ease-in-out infinite;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }
</style>
