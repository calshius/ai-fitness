<script>
    import Header from '$lib/components/Header.svelte';
    import '../app.css';
</script>

<div class="app-container">
    <Header />
    <main>
        <slot />
    </main>
</div>

<style>
    .app-container {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
        background-color: #f9fafb;
    }

    main {
        flex: 1;
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
        width: 100%;
    }

    @media (max-width: 768px) {
        main {
            padding: 1rem;
        }
    }
</style>
