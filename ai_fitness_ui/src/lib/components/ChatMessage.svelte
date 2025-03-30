<script>
    import { onMount } from 'svelte';
    import { fade } from 'svelte/transition';
    
    export let message;
    export let isUser;
    
    let formattedText;
    let showRecipes = true;
    
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
                    line.toUpperCase().includes('SUMMARY:') ||
                    line.toUpperCase().includes('FOOD SUGGESTIONS:')) {
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
            
            {#if message.recipes && Object.keys(message.recipes).length > 0}
                <div class="recipes-container">
                    <div class="recipes-header">
                        <h3>Your Meal Recipes</h3>
                        <button class="toggle-button" on:click={() => showRecipes = !showRecipes}>
                            {showRecipes ? 'Hide recipes' : 'Show recipes'}
                        </button>
                    </div>
                    
                    {#if showRecipes}
                        {#each Object.entries(message.recipes) as [mealType, recipe]}
                            <div class="recipe-card">
                                <div class="recipe-header">
                                    <h4>{recipe.name}</h4>
                                    <p class="meal-type">{mealType.charAt(0).toUpperCase() + mealType.slice(1)}</p>
                                </div>
                                
                                <div class="recipe-content">
                                    <div class="recipe-section ingredients-section">
                                        <h5>Ingredients</h5>
                                        <ul class="ingredients-list">
                                            {#each recipe.ingredients as ingredient}
                                                <li>
                                                    <span class="ingredient-name">{ingredient.name}</span>
                                                    <div class="ingredient-details">
                                                        <span class="ingredient-price">£{ingredient.price.toFixed(2)}</span>
                                                        <span class="ingredient-source">{ingredient.supermarket}</span>
                                                    </div>
                                                </li>
                                            {/each}
                                        </ul>
                                    </div>
                                    
                                    <div class="recipe-section instructions-section">
                                        <h5>Instructions</h5>
                                        <ol class="instructions-list">
                                            {#each recipe.instructions as instruction}
                                                <li>{instruction}</li>
                                            {/each}
                                        </ol>
                                    </div>
                                </div>
                                
                                <div class="recipe-macros">
                                    <h5>Macros</h5>
                                    <div class="macros-grid">
                                        <div class="macro-item">
                                            <span class="macro-label">Protein</span>
                                            <span class="macro-value">{recipe.macros.protein}g</span>
                                        </div>
                                        <div class="macro-item">
                                            <span class="macro-label">Carbs</span>
                                            <span class="macro-value">{recipe.macros.carbs}g</span>
                                        </div>
                                        <div class="macro-item">
                                            <span class="macro-label">Fat</span>
                                            <span class="macro-value">{recipe.macros.fat}g</span>
                                        </div>
                                        <div class="macro-item">
                                            <span class="macro-label">Calories</span>
                                            <span class="macro-value">{recipe.macros.calories}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        {/each}
                    {/if}
                </div>
            {/if}
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
    
    /* Recipe styles */
    .recipes-container {
        margin-top: 1.5rem;
        border-top: 1px solid #e5e7eb;
        padding-top: 1rem;
    }
    
    .recipes-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .toggle-button {
        background-color: transparent;
        color: #3b82f6;
        border: 1px solid #3b82f6;
        border-radius: 0.25rem;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        cursor: pointer;
    }
    
    .recipe-card {
        background-color: white;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        overflow: hidden;
    }
    
    .recipe-header {
        background-color: #3b82f6;
        color: white;
        padding: 0.75rem 1rem;
    }
    
    .recipe-header h4 {
        margin: 0;
        font-size: 1rem;
    }
    
    .meal-type {
        margin: 0;
        font-size: 0.75rem;
        opacity: 0.9;
    }
    
    .recipe-content {
        padding: 1rem;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }
    
    @media (max-width: 768px) {
        .recipe-content {
            grid-template-columns: 1fr;
        }
    }
    
    .recipe-section {
        margin-bottom: 1rem;
    }
    
    .recipe-section h5 {
        margin: 0 0 0.5rem 0;
        font-size: 0.875rem;
        color: #4b5563;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .ingredients-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    
    .ingredients-list li {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid #f3f4f6;
    }
    
    .ingredient-name {
        font-weight: 500;
    }
    
    .ingredient-details {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        font-size: 0.75rem;
    }
    
    .ingredient-price {
        font-weight: 600;
        color: #059669;
    }
    
    .ingredient-source {
        color: #6b7280;
    }
    
    .instructions-list {
        padding-left: 1.5rem;
        margin: 0;
    }
    
    .instructions-list li {
        margin-bottom: 0.75rem;
        line-height: 1.5;
    }
    
    .recipe-macros {
        background-color: #f9fafb;
        padding: 1rem;
        border-top: 1px solid #e5e7eb;
    }
    
    .macros-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.5rem;
    }
    
    @media (max-width: 640px) {
        .macros-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    .macro-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }
    
    .macro-label {
        font-size: 0.75rem;
        color: #6b7280;
    }
    
    .macro-value {
        font-weight: 600;
        color: #1f2937;
    }
</style>
