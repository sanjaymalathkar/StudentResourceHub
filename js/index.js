let index = 0;
function slideShow() {
    const slides = document.querySelector('.slides');
    slides.style.transform = `translateX(${-index * 100}%)`;
    index = (index + 1) % 1;
}
setInterval(slideShow, 3000);
// === DYNAMIC THEME CHANGER BASED ON TIME ===
document.addEventListener("DOMContentLoaded", function() {
    let hours = new Date().getHours();
    if (hours >= 6 && hours < 18) {
        document.body.style.background = "linear-gradient(135deg, #87CEEB, #4682B4)"; // Day mode
    } else {
        document.body.style.background = "linear-gradient(135deg, #000428, #004e92)"; // Night mode
    }
});

// === PARALLAX 3D HOVER EFFECT ===
document.addEventListener("mousemove", function(event) {
    let x = (window.innerWidth / 2 - event.pageX) / 25;
    let y = (window.innerHeight / 2 - event.pageY) / 25;
    
    document.querySelector("header").style.transform = `rotateY(${x}deg) rotateX(${y}deg)`;
    document.querySelector(".nav-menu").style.transform = `translateX(${x}px)`;
    document.querySelector(".slider").style.transform = `rotateY(${x}deg)`;
});

// === SMOOTH SCROLLING ANIMATION ===
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", function(e) {
        e.preventDefault();
        document.querySelector(this.getAttribute("href")).scrollIntoView({
            behavior: "smooth"
        });
    });
});

// === ELEMENTS FADE-IN ANIMATION WHEN SCROLLING ===
let fadeElements = document.querySelectorAll(".fade-in");

function fadeInOnScroll() {
    fadeElements.forEach((element) => {
        let position = element.getBoundingClientRect().top;
        let screenHeight = window.innerHeight;
        if (position < screenHeight - 100) {
            element.classList.add("visible");
        }
    });
}

window.addEventListener("scroll", fadeInOnScroll);
fadeInOnScroll(); // Call once to check on load

// === BACKGROUND PARTICLE EFFECT ===
const particles = [];
const numParticles = 50;
const canvas = document.createElement("canvas");
const ctx = canvas.getContext("2d");
document.body.appendChild(canvas);
canvas.style.position = "fixed";
canvas.style.top = "0";
canvas.style.left = "0";
canvas.style.zIndex = "-1";
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

class Particle {
    constructor() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.radius = Math.random() * 3 + 1;
        this.speedX = Math.random() * 2 - 1;
        this.speedY = Math.random() * 2 - 1;
    }

    move() {
        this.x += this.speedX;
        this.y += this.speedY;
        if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
        if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;
    }

    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
        ctx.fill();
    }
}

for (let i = 0; i < numParticles; i++) {
    particles.push(new Particle());
}

function animateParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach((particle) => {
        particle.move();
        particle.draw();
    });
    requestAnimationFrame(animateParticles);
}

animateParticles();

// === RESPONSIVE NAV MENU TOGGLE FOR MOBILE ===
const menuToggle = document.createElement("div");
menuToggle.innerHTML = "&#9776;";
menuToggle.style.cssText = "font-size:30px;color:white;cursor:pointer;display:none;position:fixed;top:20px;right:20px;z-index:100;";
document.body.appendChild(menuToggle);

const navMenu = document.querySelector(".nav-menu");

menuToggle.addEventListener("click", function() {
    if (navMenu.style.display === "flex") {
        navMenu.style.display = "none";
    } else {
        navMenu.style.display = "flex";
        navMenu.style.flexDirection = "column";
        navMenu.style.position = "fixed";
        navMenu.style.top = "60px";
        navMenu.style.right = "20px";
        navMenu.style.background = "rgba(0, 0, 0, 0.9)";
        navMenu.style.borderRadius = "10px";
        navMenu.style.padding = "20px";
    }
});

// Show menu toggle button only on mobile screens
window.addEventListener("resize", function() {
    if (window.innerWidth <= 768) {
        menuToggle.style.display = "block";
        navMenu.style.display = "none";
    } else {
        menuToggle.style.display = "none";
        navMenu.style.display = "flex";
    }
});

window.dispatchEvent(new Event("resize"));
