<script>
    import { onMount } from 'svelte';
    import { fade } from 'svelte/transition';
    
    export let message;
    export let isUser;
    
    let formattedText;
    
    // Format the message text to handle markdown-like formatting
    onMount(() => {
        if (!isUser) {
            // Process AI response to handle sections and bullet points
            let sections = [];
            let currentSection = { title: '', content: [] };
            let lines = message.text.split('\n');
            
            for (let line of lines) {
                if (line.toUpperCase().includes('OBSERVATIONS:') || 
                    line.toUpperCase().includes('DIETARY SUGGESTIONS:') || 
                    line.toUpperCase().includes('SUMMARY:')) {
                    // Start a new section
                    if (currentSection.title) {
                        sections.push(currentSection);
                    }
                    currentSection = { 
                        title: line.trim(), 
                        content: [] 
                    };
                } else if (line.trim().startsWith('-') || line.trim().startsWith('•')) {
                    // Add bullet point
                    currentSection.content.push({
                        type: 'bullet',
                        text: line.trim().substring(1).trim()
                    });
                } else if (line.trim()) {
                    // Add regular text
                    currentSection.content.push({
                        type: 'text',
                        text: line.trim()
                    });
                }
            }
            
            // Add the last section
            if (currentSection.title) {
                sections.push(currentSection);
            }
            
            formattedText = sections;
        } else {
            formattedText = message.text;
        }
    });
</script>

<div class="message-container {isUser ? 'user' : 'ai'}" transition:fade={{ duration: 150 }}>
    <div class="avatar">
        {#if isUser}
            <img src="/images/wiz-avatar.png" alt="User" />
        {:else}
            <div class="ai-avatar">AI</div>
        {/if}
    </div>
    <div class="message">
        {#if isUser}
            <p>{message.text}</p>
        {:else if formattedText}
            {#each formattedText as section}
                {#if section.title}
                    <h3>{section.title}</h3>
                {/if}
                {#each section.content as item}
                    {#if item.type === 'bullet'}
                        <div class="bullet-point">
                            <span class="bullet">•</span>
                            <span>{item.text}</span>
                        </div>
                    {:else}
                        <p>{item.text}</p>
                    {/if}
                {/each}
            {/each}
        {/if}
        <div class="timestamp">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
    </div>
</div>

<style>
    .message-container {
        display: flex;
        margin-bottom: 1.5rem;
        gap: 1rem;
    }

    .user {
        justify-content: flex-end;
    }

    .ai {
        justify-content: flex-start;
    }

    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        overflow: hidden;
        flex-shrink: 0;
    }

    .avatar img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .ai-avatar {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
    }

    .message {
        max-width: 70%;
        padding: 1rem;
        border-radius: 1rem;
        position: relative;
    }

    .user .message {
        background-color: #3b82f6;
        color: white;
        border-top-right-radius: 0;
    }

    .ai .message {
        background-color: #f3f4f6;
        color: #333;
        border-top-left-radius: 0;
    }

    .message p {
        margin: 0 0 0.5rem 0;
        line-height: 1.5;
    }

    .message h3 {
        margin: 0.5rem 0;
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e40af;
    }

    .bullet-point {
        display: flex;
        margin-bottom: 0.5rem;
        align-items: flex-start;
    }

    .bullet {
        margin-right: 0.5rem;
        color: #3b82f6;
        font-weight: bold;
    }

    .timestamp {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.7);
        position: absolute;
        bottom: 0.5rem;
        right: 1rem;
    }

    .ai .timestamp {
        color: rgba(0, 0, 0, 0.5);
    }
</style>
