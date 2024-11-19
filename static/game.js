let gameOver = false;
let gridCells = [];

document.addEventListener('DOMContentLoaded', () => {
    fetchGameState(true);

    document.addEventListener('keydown', (event) => {
        if (gameOver) return;

        let move = null;
        switch (event.key) {
            case 'ArrowUp':
                move = 'UP';
                break;
            case 'ArrowDown':
                move = 'DOWN';
                break;
            case 'ArrowLeft':
                move = 'LEFT';
                break;
            case 'ArrowRight':
                move = 'RIGHT';
                break;
            case 'Enter':
                move = 'STAY';
                break;
            default:
                return; // Ignore other keys
        }
        makeMove(move);
    });

    // Handle Reset Button
    const resetButton = document.getElementById('reset-button');
    resetButton.addEventListener('click', () => {
        fetch('/reset', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            gameOver = data.game_over;
            document.getElementById('message').innerText = data.message;
            fetchGameState(true); // Re-render the grid
        });
    });
});

function fetchGameState(initial = false) {
    fetch('/game_state')
        .then(response => response.json())
        .then(data => {
            if (initial) {
                renderGrid(data.grid);
            } else {
                updateGrid(data.grid);
            }
            document.getElementById('message').innerText = data.message;
            gameOver = data.game_over;
        });
}

function makeMove(move) {
    fetch('/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ move: move })
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById('message').innerText = data.message;
            gameOver = data.game_over;

            if (data.game_over) {
                // If game over, fetch the latest grid state
                fetchGameState();
            } else {
                animateMovements(data);
            }
        });
}

function renderGrid(grid) {
    const container = document.getElementById('game-container');
    container.innerHTML = '';
    gridCells = [];
    grid.forEach((row, rowIndex) => {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'grid-row';
        const rowCells = [];
        row.forEach((cell, colIndex) => {
            const cellDiv = document.createElement('div');
            cellDiv.className = 'grid-cell';
            cellDiv.innerText = cell;
            cellDiv.setAttribute('data-row', rowIndex);
            cellDiv.setAttribute('data-col', colIndex);
            rowDiv.appendChild(cellDiv);
            rowCells.push(cellDiv);
        });
        container.appendChild(rowDiv);
        gridCells.push(rowCells);
    });
}

function updateGrid(grid) {
    grid.forEach((row, rowIndex) => {
        row.forEach((cell, colIndex) => {
            const cellDiv = gridCells[rowIndex][colIndex];
            cellDiv.innerText = cell;
            cellDiv.className = 'grid-cell'; // Reset classes
        });
    });
}

function animateMovements(data) {
    const playerMove = data.player_move;
    const droneMoves = data.drone_moves;

    // Create a Promise for each movement to handle animation timing
    const animations = [];

    // Player movement
    if (playerMove) {
        const fromCell = gridCells[playerMove.from[0]][playerMove.from[1]];
        const toCell = gridCells[playerMove.to[0]][playerMove.to[1]];

        animations.push(animateMove(fromCell, toCell, 'player'));
    }

    // Drone movements
    if (droneMoves) {
        droneMoves.forEach(droneMove => {
            const fromCell = gridCells[droneMove.from[0]][droneMove.from[1]];
            const toCell = gridCells[droneMove.to[0]][droneMove.to[1]];

            animations.push(animateMove(fromCell, toCell, 'drone', droneMove.symbol));
        });
    }

    // Wait for all animations to complete before updating the grid
    Promise.all(animations).then(() => {
        fetchGameState(); // Update the grid after animations
    });
}

function animateMove(fromCell, toCell, type, symbol = '') {
    return new Promise(resolve => {
        const movingElement = document.createElement('div');
        movingElement.className = 'moving-piece ' + type;
        if (type === 'drone') {
            movingElement.innerText = symbol;
        } else {
            movingElement.innerText = fromCell.innerText;
        }

        const container = document.getElementById('game-container');
        container.appendChild(movingElement);

        // Get positions
        const containerRect = container.getBoundingClientRect();
        const fromRect = fromCell.getBoundingClientRect();
        const toRect = toCell.getBoundingClientRect();

        // Set initial position relative to container
        movingElement.style.position = 'absolute';
        movingElement.style.left = (fromRect.left - containerRect.left) + 'px';
        movingElement.style.top = (fromRect.top - containerRect.top) + 'px';
        movingElement.style.width = fromRect.width + 'px';
        movingElement.style.height = fromRect.height + 'px';
        movingElement.style.lineHeight = fromRect.height + 'px';
        movingElement.style.textAlign = 'center';

        // Trigger reflow for CSS transition
        movingElement.offsetWidth;

        // Set transition
        movingElement.style.transition = 'all 0.5s linear';

        // Move to new position
        movingElement.style.left = (toRect.left - containerRect.left) + 'px';
        movingElement.style.top = (toRect.top - containerRect.top) + 'px';

        // After transition, remove movingElement
        movingElement.addEventListener('transitionend', () => {
            movingElement.parentNode.removeChild(movingElement);
            resolve();
        });
    });
}