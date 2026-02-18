// Based on: https://medium.com/@jadomene99/integrating-your-opencv-project-into-a-react-component-using-flask-6bcf909c07f4

import React, { useState } from "react";

function Game(gameId) {
    return (
        <div 
            class="crop"
            style="position:relative;height:0;padding-bottom:117.6%;overflow:hidden;"
        >
            <iframe
                style="position:absolute;top:0;left:0;width:100%;height:100%;"
                src={"https://arcade.makecode.com/---run?id=" + gameId}
                allowfullscreen="allowfullscreen"
                sandbox="allow-popups allow-forms allow-scripts allow-same-origin"
                frameborder="0"
            >
            </iframe>
        </div>
    );
}

function Cam() {
    return (
        <div>
            <img
                src="http://localhost:5000/video_feed"
                alt="Video"
            />
        </div>
    );
};

export default Cam;
