let gameOver = false;
let gridCells = [];
const EMPTY_SYMBOL = '.';
let startBox = null; // Global variable to hold start box data

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
            startBox = data.start_box; // Update startBox variable
            if (initial) {
                renderGrid(data.grid, startBox);
            } else {
                updateGrid(data.grid, startBox);
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

function renderGrid(grid, startBox) {
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

    // Now render the start box cell
    const startBoxDiv = document.createElement('div');
    startBoxDiv.className = 'grid-cell start-box';
    startBoxDiv.innerText = startBox.symbol;
    startBoxDiv.style.position = 'absolute';
    startBoxDiv.style.width = '30px';
    startBoxDiv.style.height = '30px';
    startBoxDiv.style.lineHeight = '30px';
    startBoxDiv.style.textAlign = 'center';
    startBoxDiv.style.border = '1px solid #ccc';
    startBoxDiv.style.backgroundColor = '#f9f9f9'; // Optional styling

    // Position the start box cell relative to the grid
    const containerRect = container.getBoundingClientRect();

    // Assume each cell is 30px x 30px
    const cellSize = 30;

    let left = 0;
    let top = 0;

    if (startBox.position[0] === -1) {
        // Start box is above the grid
        top = -cellSize;
        left = startBox.position[1] * cellSize;
    } else if (startBox.position[0] === grid.length) {
        // Start box is below the grid
        top = grid.length * cellSize;
        left = startBox.position[1] * cellSize;
    } else if (startBox.position[1] === -1) {
        // Start box is to the left of the grid
        top = startBox.position[0] * cellSize;
        left = -cellSize;
    } else if (startBox.position[1] === grid[0].length) {
        // Start box is to the right of the grid
        top = startBox.position[0] * cellSize;
        left = grid[0].length * cellSize;
    }

    startBoxDiv.style.left = left + 'px';
    startBoxDiv.style.top = top + 'px';

    container.appendChild(startBoxDiv);

    // Save the startBoxDiv for later use
    window.startBoxDiv = startBoxDiv;
}

function updateGrid(grid, startBox) {
    grid.forEach((row, rowIndex) => {
        row.forEach((cell, colIndex) => {
            const cellDiv = gridCells[rowIndex][colIndex];
            cellDiv.innerText = cell;
            cellDiv.className = 'grid-cell'; // Reset classes
        });
    });

    // Update the start box cell
    if (window.startBoxDiv) {
        window.startBoxDiv.innerText = startBox.symbol;
    }
}

function animateMovements(data) {
    const playerMove = data.player_move;
    const droneMoves = data.drone_moves;

    // Update startBox variable
    if (data.start_box) {
        startBox = data.start_box;
    }

    // Create a Promise for each movement to handle animation timing
    const animations = [];

    // Player movement
    if (playerMove && (playerMove.from[0] !== playerMove.to[0] || playerMove.from[1] !== playerMove.to[1])) {
        const fromPos = playerMove.from;
        const toPos = playerMove.to;

        const fromCell = getCell(fromPos[0], fromPos[1]);
        const toCell = getCell(toPos[0], toPos[1]);

        animations.push(animateMove(fromCell, toCell, 'player', 'P'));
    }

    // Drone movements
    if (droneMoves) {
        droneMoves.forEach(droneMove => {
            if (droneMove.from[0] === droneMove.to[0] && droneMove.from[1] === droneMove.to[1]) {
                return; // Skip if the drone didn't move
            }
            const fromCell = getCell(droneMove.from[0], droneMove.from[1]);
            const toCell = getCell(droneMove.to[0], droneMove.to[1]);

            animations.push(animateMove(fromCell, toCell, 'drone', droneMove.symbol));
        });
    }

    // Wait for all animations to complete before updating the grid
    Promise.all(animations).then(() => {
        // Update the grid after animations
        fetchGameState();
    });
}

function getCell(row, col) {
    // Ensure positions are numbers
    row = Number(row);
    col = Number(col);
    const startRow = Number(startBox.position[0]);
    const startCol = Number(startBox.position[1]);

    if (row >= 0 && row < gridCells.length && col >= 0 && col < gridCells[0].length) {
        return gridCells[row][col];
    } else if (startBox && row === startRow && col === startCol) {
        // Return the start box cell
        return window.startBoxDiv;
    }
    return null;
}

function animateMove(fromCell, toCell, type, symbol = '') {
    return new Promise(resolve => {
        const movingElement = document.createElement('div');
        movingElement.className = 'moving-piece ' + type;
        movingElement.innerText = symbol;

        const container = document.getElementById('game-container');
        container.appendChild(movingElement);

        // Get positions
        const containerRect = container.getBoundingClientRect();

        // Set initial position
        if (fromCell) {
            const fromRect = fromCell.getBoundingClientRect();
            movingElement.style.left = (fromRect.left - containerRect.left) + 'px';
            movingElement.style.top = (fromRect.top - containerRect.top) + 'px';
            fromCell.innerText = EMPTY_SYMBOL;
        } else {
            // Starting from outside the grid (adjust as needed)
            movingElement.style.left = '-30px';
            movingElement.style.top = '0px';
        }

        movingElement.style.width = '30px';
        movingElement.style.height = '30px';
        movingElement.style.lineHeight = '30px';
        movingElement.style.textAlign = 'center';

        // Trigger reflow for CSS transition
        movingElement.offsetWidth;

        // Set transition
        movingElement.style.transition = 'all 0.5s linear';

        // Move to new position
        if (toCell) {
            const toRect = toCell.getBoundingClientRect();
            movingElement.style.left = (toRect.left - containerRect.left) + 'px';
            movingElement.style.top = (toRect.top - containerRect.top) + 'px';
            toCell.innerText = EMPTY_SYMBOL;
        } else {
            // Moving outside the grid (adjust as needed)
            movingElement.style.left = '-30px';
            movingElement.style.top = '0px';
        }

        // After transition, remove movingElement
        movingElement.addEventListener('transitionend', () => {
            movingElement.parentNode.removeChild(movingElement);
            resolve();
        });
    });
}

function isWithinGrid(pos) {
    const row = Number(pos[0]);
    const col = Number(pos[1]);
    const startRow = Number(startBox.position[0]);
    const startCol = Number(startBox.position[1]);

    if (row === startRow && col === startCol) {
        return true;
    }
    return row >= 0 && row < gridCells.length && col >= 0 && col < gridCells[0].length;
}