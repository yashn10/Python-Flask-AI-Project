document.addEventListener("DOMContentLoaded", () => {
    // Register ScrollTrigger if available (prevents console errors if plugin fails to load)
    if (window.ScrollTrigger && gsap && gsap.registerPlugin) {
        gsap.registerPlugin(ScrollTrigger);
    }

    // Fade in main content
    gsap.from("main", {
        opacity: 0,
        y: 50,
        duration: 1,
        ease: "power3.out"
    });

    // Animate cards on scroll
    gsap.utils.toArray(".card").forEach(card => {
        const config = {
            opacity: 0,
            y: 30,
            duration: 0.8
        };

        // Only add scrollTrigger if the plugin is present
        if (window.ScrollTrigger) {
            config.scrollTrigger = {
                trigger: card,
                start: "top 85%"
            };
        }

        gsap.from(card, config);
    });

    // Animate fullscreen modal
    const modal = document.getElementById('fullscreen-modal');
    const fullscreenImg = document.getElementById('fullscreen-image');

    // Open modal animation
    window.openFullscreen = function (src) {
        fullscreenImg.src = src;
        modal.classList.remove('hidden');
        gsap.fromTo(fullscreenImg,
            { opacity: 0, scale: 0.8 },
            { opacity: 1, scale: 1, duration: 0.5, ease: "power3.out" }
        );
    };

    // Close modal animation
    window.closeFullscreen = function () {
        gsap.to(fullscreenImg, {
            opacity: 0,
            scale: 0.8,
            duration: 0.3,
            ease: "power3.in",
            onComplete: () => {
                modal.classList.add('hidden');
            }
        });
    };
});