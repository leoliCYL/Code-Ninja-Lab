
const eventStream = new EventSource("/event_stream");

function setBodyHtml(contents) {
    let body = document.getElementById("site-contents");
    body.innerHTML = contents;
}

function startGameScreen(gameId) {
    setBodyHtml(
        '<div class="game-container">'
        + '<iframe'
        + ' id="game"'
        + ' class="game-frame"'
        + ` src="https://arcade.makecode.com/---run?id=${gameId}"`
        + ' allowfullscreen="allowfullscreen"'
        + ' sandbox="allow-popups allow-forms allow-scripts allow-same-origin" frameborder="0"></iframe>'
        + '</div>'
    );
}

function startCameraScreen() {
    setBodyHtml('<div><img id="video" src="/video_feed" alt="Error: Video stream unavailable" /></div>');
}

eventStream.onmessage = function(event) {
    const message = JSON.parse(event.data);
    switch (message.state) {
        case 'GRANTED':
            startGameScreen("_Xxt7bpDMHDwk");
            let game = document.getElementById("game");
            game.focus();
            break;
        default:
            startCameraScreen();
            break;
    }
}
