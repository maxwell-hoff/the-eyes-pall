let gameOver = false;

document.addEventListener('DOMContentLoaded', () => {
    fetchGameState();

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
            fetchGameState();
        });
    });
});

function fetchGameState() {
    fetch('/game_state')
        .then(response => response.json())
        .then(data => {
            renderGrid(data.grid);
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
            fetchGameState();
        });
}

function renderGrid(grid) {
    const container = document.getElementById('game-container');
    container.innerHTML = '';
    grid.forEach(row => {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'grid-row';
        row.forEach(cell => {
            const cellDiv = document.createElement('div');
            cellDiv.className = 'grid-cell';
            cellDiv.innerText = cell;
            rowDiv.appendChild(cellDiv);
        });
        container.appendChild(rowDiv);
    });
}