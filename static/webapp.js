
const eventStream = new EventSource("/event_stream");

function setBodyHtml(contents) {
    let body = document.getElementById("site-contents");
    body.innerHTML = contents;
}

function startGameScreen(gameId) {
    const isFullUrl = gameId.startsWith('http');
    const src = isFullUrl ? gameId : `https://arcade.makecode.com/---run?id=${gameId}`;
    const frameClass = isFullUrl ? 'game-frame-direct' : 'game-frame';

    setBodyHtml(
        '<div class="game-container">'
        + `<iframe id="game" class="${frameClass}"`
        + ` src="${src}"`
        + ' allowfullscreen="allowfullscreen"'
        + ' sandbox="allow-popups allow-forms allow-scripts allow-same-origin" frameborder="0">'
        + '</iframe>'
        + '</div>'
    );
}

function startCameraScreen() {
    setBodyHtml('<div><img id="video" src="/video_feed" alt="Error: Video stream unavailable" /></div>');
}

eventStream.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log(message);
    switch (message.state) {
        case 'GRANTED':
            if (message.gameId !== "") {
                startGameScreen(message.gameId);
            }
            break;
        default:
            startCameraScreen();
            break;
    }
};

window.onload = function() {};
