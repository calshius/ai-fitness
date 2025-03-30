import { writable } from 'svelte/store';

function createChatStore() {
    const { subscribe, set, update } = writable({
        messages: [],
        isLoading: false,
        selectedModel: "mistralai/Mistral-7B-Instruct-v0.2"
    });

    return {
        subscribe,
        addMessage: (text, isUser, includeRecipes = false, recipes = null) => {
            update(store => {
                const newMessage = {
                    id: Date.now(),
                    text,
                    isUser,
                    timestamp: new Date(),
                    includeRecipes,
                    recipes
                };
                return {
                    ...store,
                    messages: [...store.messages, newMessage]
                };
            });
        },
        setLoading: (isLoading) => {
            update(store => ({ ...store, isLoading }));
        },
        setModel: (model) => {
            update(store => ({ ...store, selectedModel: model }));
        },
        clear: () => {
            update(store => ({ ...store, messages: [] }));
        }
    };
}

export const chatStore = createChatStore();
