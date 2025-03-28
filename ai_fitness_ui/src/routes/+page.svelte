<script>
    import { onMount } from 'svelte';
    import { chatStore } from '$lib/stores/chatStore';
    import { queryFitnessData } from '$lib/api';
    import ChatInput from '$lib/components/ChatInput.svelte';
    import ChatMessage from '$lib/components/ChatMessage.svelte';
    import Sidebar from '$lib/components/Sidebar.svelte';

    let chatContainer;
    let messages = [];

    // Subscribe to the chat store
    $: messages = $chatStore.messages;

    // Handle new query submission
    async function handleSubmit(event) {
        const query = event.detail;
        
        // Set loading state
        chatStore.setLoading(true);
        
        try {
            // Get response from API
            const response = await queryFitnessData(query);
            
            // Add AI response to chat
            chatStore.addMessage(response, false);
        } catch (error) {
            console.error('Error querying fitness data:', error);
            chatStore.addMessage('Sorry, there was an error processing your request. Please try again.', false);
        } finally {
            chatStore.setLoading(false);
        }
    }

    // Listen for suggested questions from sidebar
    onMount(() => {
        const handleAskQuestion = (event) => {
            handleSubmit({ detail: event.detail });
        };
        
        window.addEventListener('ask-question', handleAskQuestion);
        
        return () => {
            window.removeEventListener('ask-question', handleAskQuestion);
        };
    });

    // Scroll to bottom when messages change
    $: if (chatContainer && messages.length) {
        setTimeout(() => {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 0);
    }
</script>

<svelte:head>
    <title>AI Fitness - Chat</title>
</svelte:head>

<div class="chat-page">
    <Sidebar />
    
    <div class="chat-container">
        <div class="chat-messages" bind:this={chatContainer}>
            {#if messages.length === 0}
                <div class="welcome-message">
                    <h1>Welcome to AI Fitness</h1>
                    <p>Ask questions about your fitness and nutrition data to get personalized insights and recommendations.</p>
                    <p>Try asking about your calorie intake, exercise patterns, or weight trends.</p>
                </div>
            {:else}
                {#each messages as message (message.id)}
                    <ChatMessage {message} isUser={message.isUser} />
                {/each}
            {/if}
            
            {#if $chatStore.isLoading}
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            {/if}
        </div>
        
        <div class="chat-input-container">
            <ChatInput on:submit={handleSubmit} />
        </div>
    </div>
</div>

<style>
    .chat-page {
        display: flex;
        height: calc(100vh - 80px); /* Adjust based on header height */
    }

    .chat-container {
        flex: 1;
        display: flex;
        flex-direction: column;
        background-color: #ffffff;
        border-radius: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        overflow: hidden;
    }

    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 2rem;
        display: flex;
        flex-direction: column;
    }

    .welcome-message {
        text-align: center;
        margin: auto;
        max-width: 600px;
        color: #6b7280;
    }

    .welcome-message h1 {
        color: #3b82f6;
        margin-bottom: 1rem;
    }

    .chat-input-container {
        padding: 1rem 2rem;
        border-top: 1px solid #e5e7eb;
    }

    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        padding: 1rem;
        align-self: flex-start;
    }

    .typing-indicator span {
        width: 8px;
        height: 8px;
        background-color: #d1d5db;
        border-radius: 50%;
        display: inline-block;
        animation: bounce 1.5s infinite ease-in-out;
    }

    .typing-indicator span:nth-child(1) {
        animation-delay: 0s;
    }

    .typing-indicator span:nth-child(2) {
        animation-delay: 0.2s;
    }

    .typing-indicator span:nth-child(3) {
        animation-delay: 0.4s;
    }

    @keyframes bounce {
        0%, 60%, 100% {
            transform: translateY(0);
        }
        30% {
            transform: translateY(-4px);
        }
    }

    @media (max-width: 768px) {
        .chat-page {
            flex-direction: column;
            height: auto;
        }
        
        .chat-container {
            height: calc(100vh - 200px); /* Adjust based on header and sidebar height */
        }
    }
</style>
