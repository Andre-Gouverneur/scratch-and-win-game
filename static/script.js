// Get references to our HTML elements
const registrationForm = document.getElementById('registration-form');
const gameArea = document.getElementById('game-area');
const scratchGrid = document.getElementById('scratch-grid');
const prizeDisplay = document.getElementById('prize-display');

// Constants for the scratch effect
const SCRATCH_RADIUS = 30;
const SCRATCH_THRESHOLD = 0.5;

let scratchedCardsCount = 0;
let finalPrize = "NO_PRIZE";
let totalCards = 0;

// Listen for when the registration form is submitted
registrationForm.addEventListener('submit', async function(event) {
    event.preventDefault();
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;

    try {
        const response = await fetch('http://127.0.0.1:5000/api/get-prize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, email: email })
        });
        const prizeData = await response.json();

        registrationForm.style.display = 'none';
        gameArea.style.display = 'block';

        initializeScratchCards(prizeData.results, prizeData.prize);

    } catch (error) {
        console.error('Error:', error);
        prizeDisplay.innerHTML = '<p>Something went wrong. Please try again.</p>';
        prizeDisplay.style.display = 'block';
    }
});

function initializeScratchCards(results, winningPrize) {
    scratchGrid.innerHTML = '';
    scratchedCardsCount = 0;
    finalPrize = winningPrize;
    totalCards = results.length;

    results.forEach((symbol, index) => {
        const card = document.createElement('div');
        card.className = 'scratch-card';

        const symbolEl = document.createElement('div');
        symbolEl.className = 'prize-symbol';
        symbolEl.textContent = symbol.replace(/_/g, ' ');
        card.appendChild(symbolEl);
        
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.className = 'scratch-canvas';
        canvas.width = 300;
        canvas.height = 300;
        card.appendChild(canvas);
        
        ctx.fillStyle = '#007bff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        let isScratching = false;
        let isCardFullyScratched = false; // Flag to prevent multiple increments

        function startScratching(e) {
            e.preventDefault();
            isScratching = true;
            scratch(e);
        }
        
        function stopScratching() {
            isScratching = false;
        }

        function scratch(e) {
            if (!isScratching) return;
            const rect = canvas.getBoundingClientRect();
            const x = (e.clientX || e.touches[0].clientX) - rect.left;
            const y = (e.clientY || e.touches[0].clientY) - rect.top;
            
            ctx.globalCompositeOperation = 'destination-out';
            ctx.beginPath();
            ctx.arc(x * (canvas.width / rect.width), y * (canvas.height / rect.height), SCRATCH_RADIUS, 0, 2 * Math.PI);
            ctx.fill();
            
            if (!isCardFullyScratched && checkScratchCompletion(canvas, ctx)) {
                isCardFullyScratched = true; // Mark this card as fully scratched
                scratchedCardsCount++; // Increment the global counter once
                
                if (scratchedCardsCount === totalCards) {
                    setTimeout(() => {
                        showFinalPrize(finalPrize);
                    }, 500);
                }
            }
        }
        
        card.addEventListener('mousedown', startScratching);
        card.addEventListener('mousemove', scratch);
        card.addEventListener('mouseup', stopScratching);
        card.addEventListener('mouseleave', stopScratching);
        card.addEventListener('touchstart', startScratching);
        card.addEventListener('touchmove', scratch);
        card.addEventListener('touchend', stopScratching);
        
        scratchGrid.appendChild(card);
    });
}

function checkScratchCompletion(canvas, ctx) {
    const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const totalPixels = pixels.data.length / 4;
    let transparentPixels = 0;

    for (let i = 0; i < pixels.data.length; i += 4) {
        if (pixels.data[i + 3] === 0) {
            transparentPixels++;
        }
    }
    return (transparentPixels / totalPixels) > SCRATCH_THRESHOLD;
}

function showFinalPrize(prize) {
    let prizeMessage = '';
    if (prize && prize !== "NO_PRIZE") {
        prizeMessage = `<h3>Congratulations! You've won:</h3><img src="/static/images/${prize}.png" alt="${prize}" class="prize-image">`;
    } else {
        prizeMessage = `<h3>No prize this time. Try again!</h3><img src="/static/images/no_prize.png" alt="No prize" class="prize-image">`;
    }
    
    prizeDisplay.innerHTML = `
        ${prizeMessage}
        <button id="play-again-btn" style="margin-top: 20px; padding: 10px 20px; font-size: 1em; cursor: pointer;">Play Again</button>
    `;

    prizeDisplay.style.display = 'block';

    document.getElementById('play-again-btn').addEventListener('click', () => {
        window.location.href = "/";
    });
}