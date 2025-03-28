<script>
    import { page } from '$app/stores';
</script>

<header>
    <div class="logo">
        <img src="/images/hat-barbell-stick.png" alt="AI Fitness Logo" />
        <h1>AI Fitness</h1>
    </div>
    <nav>
        <ul>
            <li class:active={$page.url.pathname === '/'}>
                <a href="/">Chat</a>
            </li>
            <li class:active={$page.url.pathname === '/upload'}>
                <a href="/upload">Upload Data</a>
            </li>
        </ul>
    </nav>
</header>

<style>
    header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 2rem;
        background-color: #ffffff;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        position: sticky;
        top: 0;
        z-index: 100;
    }

    .logo {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .logo img {
        height: 2.5rem;
    }

    .logo h1 {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
        margin: 0;
    }

    nav ul {
        display: flex;
        gap: 2rem;
        list-style: none;
        margin: 0;
        padding: 0;
    }

    nav a {
        color: #555;
        text-decoration: none;
        font-weight: 500;
        transition: color 0.2s, border-bottom 0.2s;
        padding-bottom: 0.25rem;
        border-bottom: 2px solid transparent;
    }

    nav a:hover {
        color: #3b82f6;
        border-bottom: 2px solid #3b82f6;
    }

    .active a {
        color: #3b82f6;
        border-bottom: 2px solid #3b82f6;
    }

    @media (max-width: 640px) {
        header {
            padding: 1rem;
        }

        .logo h1 {
            font-size: 1.25rem;
        }

        nav ul {
            gap: 1rem;
        }
    }
</style>
