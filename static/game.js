let gameOver = false;
let gridCells = [];
const EMPTY_SYMBOL = '.'; // Define EMPTY_SYMBOL
const START_BOX_SYMBOL = 'S'; // Define START_BOX_SYMBOL if needed

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
    if (playerMove && (playerMove.from[0] !== playerMove.to[0] || playerMove.from[1] !== playerMove.to[1])) {
        const fromPos = playerMove.from;
        const toPos = playerMove.to;

        // Adjust indices if grid has extra rows/columns
        const rowOffset = fromPos[0] === -1 || toPos[0] === -1 ? 1 : 0;
        const colOffset = fromPos[1] === -1 || toPos[1] === -1 ? 1 : 0;

        const fromCell = getCell(fromPos[0] + rowOffset, fromPos[1] + colOffset);
        const toCell = getCell(toPos[0] + rowOffset, toPos[1] + colOffset);

        animations.push(animateMove(fromCell, toCell, 'player', 'P'));
    }

    // Drone movements
    if (droneMoves) {
        droneMoves.forEach(droneMove => {
            if (droneMove.from[0] === droneMove.to[0] && droneMove.from[1] === droneMove.to[1]) {
                return; // Skip if the drone didn't move
            }
            const fromCell = getCell(droneMove.from[0] + 1, droneMove.from[1]);
            const toCell = getCell(droneMove.to[0] + 1, droneMove.to[1]);

            animations.push(animateMove(fromCell, toCell, 'drone', droneMove.symbol));
        });
    }

    // Wait for all animations to complete before updating the grid
    Promise.all(animations).then(() => {
        // Update the grid after animations
        fetchGameState();
    });
}

function getCell(rowIndex, colIndex) {
    if (rowIndex >= 0 && rowIndex < gridCells.length && colIndex >= 0 && colIndex < gridCells[0].length) {
        return gridCells[rowIndex][colIndex];
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
    return pos[0] >= 0 && pos[0] < gridCells.length && pos[1] >= 0 && pos[1] < gridCells[0].length;
}
