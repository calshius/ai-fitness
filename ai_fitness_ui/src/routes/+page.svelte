<script>
    import { onMount } from 'svelte';
    import { chatStore } from '$lib/stores/chatStore';
    import { queryFitnessData } from '$lib/api';
    import ChatInput from '$lib/components/ChatInput.svelte';
    import ChatMessage from '$lib/components/ChatMessage.svelte';
    import Sidebar from '$lib/components/Sidebar.svelte';

    let chatContainer;
    let messages = [];
    let userScrolled = false;
    let lastMessageCount = 0;

    // Subscribe to the chat store
    $: messages = $chatStore.messages;

    // Handle new query submission
    async function handleSubmit(event) {
        const query = event.detail;
        
        // Add user message to chat first
        chatStore.addMessage(query, true);
        
        // Reset userScrolled flag when user submits a new message
        userScrolled = false;
        
        // Set loading state
        chatStore.setLoading(true);
        
        try {
            // Get response from API with selected model
            const response = await queryFitnessData(query, $chatStore.selectedModel);
            
            // Add AI response to chat
            chatStore.addMessage(response, false);
        } catch (error) {
            console.error('Error querying fitness data:', error);
            
            // Ensure we always add an error message to the chat
            chatStore.addMessage(
                "There seems to be an issue with the model you selected, please select a different model.", 
                false
            );
        } finally {
            chatStore.setLoading(false);
        }
    }

    // Listen for suggested questions from sidebar
    onMount(() => {
        const handleAskQuestion = (event) => {
            // Don't call chatStore.addMessage here - pass directly to handleSubmit
            handleSubmit({ detail: event.detail });
        };
        
        window.addEventListener('ask-question', handleAskQuestion);
        
        // Add scroll event listener to detect user scrolling
        if (chatContainer) {
            chatContainer.addEventListener('scroll', handleScroll);
        }
        
        return () => {
            window.removeEventListener('ask-question', handleAskQuestion);
            if (chatContainer) {
                chatContainer.removeEventListener('scroll', handleScroll);
            }
        };
    });

    // Handle scroll events
    function handleScroll() {
        if (!chatContainer) return;
        
        // Check if user has scrolled up
        const { scrollTop, scrollHeight, clientHeight } = chatContainer;
        const isAtBottom = scrollTop + clientHeight >= scrollHeight - 50; // Within 50px of bottom
        
        userScrolled = !isAtBottom;
    }

    // Scroll to bottom only when new messages arrive and user hasn't scrolled up
    $: if (chatContainer && messages.length > lastMessageCount && !userScrolled) {
        lastMessageCount = messages.length;
        setTimeout(() => {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 0);
    }
    
    // Update lastMessageCount when messages change
    $: if (messages) {
        if (messages.length === 0) {
            // Reset scroll state when chat is cleared
            userScrolled = false;
            lastMessageCount = 0;
        }
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
