<script>
    import { chatStore } from '$lib/stores/chatStore';
    
    // Sample suggested questions
    const suggestedQuestions = [
        "What was my average daily calorie intake?",
        "How has my weight changed over time?",
        "What's my protein intake compared to my goals?",
        "Show me my exercise patterns for the last month",
        "What's the correlation between my workouts and weight?"
    ];
    
    function askQuestion(question) {        
        // Dispatch a custom event that the parent component can listen for
        const event = new CustomEvent('ask-question', { detail: question });
        window.dispatchEvent(event);
    }
    
    function clearChat() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            chatStore.clear();
        }
    }
</script>

<aside class="sidebar">
    <div class="sidebar-section">
        <h2>Suggested Questions</h2>
        <ul class="question-list">
            {#each suggestedQuestions as question}
                <li>
                    <button on:click={() => askQuestion(question)}>
                        {question}
                    </button>
                </li>
            {/each}
        </ul>
    </div>
    
    <div class="sidebar-section">
        <h2>Actions</h2>
        <button class="action-button" on:click={clearChat}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
            Clear Chat
        </button>
        <a href="/upload" class="action-button">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            Upload Data
        </a>
    </div>
</aside>

<style>
    .sidebar {
        background-color: #f9fafb;
        border-right: 1px solid #e5e7eb;
        padding: 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 2rem;
        width: 300px;
        height: 100%;
    }

    .sidebar-section h2 {
        font-size: 1rem;
        font-weight: 600;
        color: #4b5563;
        margin-top: 0;
        margin-bottom: 1rem;
    }

    .question-list {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .question-list button {
        background: none;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 0.75rem;
        text-align: left;
        font-size: 0.875rem;
        color: #374151;
        cursor: pointer;
        transition: all 0.2s;
        width: 100%;
    }

    .question-list button:hover {
        background-color: #f3f4f6;
        border-color: #d1d5db;
    }

    .action-button {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 0.75rem;
        font-size: 0.875rem;
        color: #374151;
        cursor: pointer;
        transition: all 0.2s;
        width: 100%;
        margin-bottom: 0.5rem;
        text-decoration: none;
        justify-content: center;
    }

    .action-button:hover {
        background-color: #f3f4f6;
        border-color: #d1d5db;
    }

    @media (max-width: 768px) {
        .sidebar {
            width: 100%;
            height: auto;
            border-right: none;
            border-bottom: 1px solid #e5e7eb;
        }
    }
</style>
