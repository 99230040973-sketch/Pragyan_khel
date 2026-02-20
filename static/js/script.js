// 1. Global State
let videoFps = 30; // Default, will be updated by server response

/**
 * Main function to handle file upload, analysis, and UI updates
 */
async function uploadVideo() {
    const fileInput = document.getElementById('videoInput');
    const btn = document.getElementById('analyzeBtn');
    const loader = document.getElementById('loader');
    const statsBar = document.getElementById('statsBar');
    const tableBody = document.querySelector('#resultsTable tbody');
    const video = document.getElementById('outputVideo');

    if (!fileInput.files[0]) {
        return alert("Please select a video file!");
    }

    // UI Feedback: Start loading
    btn.disabled = true;
    loader.style.display = "block";
    statsBar.style.display = "none";

    const formData = new FormData();
    formData.append('video', fileInput.files[0]);

    try {
        const response = await fetch('/upload', { method: 'POST', body: formData });
        const data = await response.json();

        if (data.error) throw new Error(data.error);

        // SYNC FPS: Store the actual FPS from the server for accurate frame stepping
        videoFps = data.summary.fps || 30; 

        // Update Stats Dashboard
        document.getElementById('totalFrames').innerText = data.summary.total_frames;
        document.getElementById('anomalyCount').innerText = data.summary.issues_found;
        document.getElementById('avgGap').innerText = `${data.summary.avg_gap}ms`;

        // Load Video Output
        video.src = data.video_url;
        video.load();

        // Render Results Table
        tableBody.innerHTML = data.results.map(row => {
            let cssClass = "";
            if (row.status === "Frame Drop/Lag") cssClass = "warning-row";
            else if (row.status === "Frozen/Merge") cssClass = "merge-row";

            return `
                <tr class="${cssClass}" onclick="seekTo(${row.timestamp})" style="cursor:pointer">
                    <td>${row.frame}</td>
                    <td style="font-family:monospace">${formatClockTime(row.timestamp)}</td>
                    <td>${row.gap}ms</td>
                    <td>${row.status}</td>
                </tr>
            `;
        }).join('');

        statsBar.style.display = "flex";

    } catch (err) {
        alert("System Error: " + err.message);
    } finally {
        btn.disabled = false;
        loader.style.display = "none";
    }
}

/**
 * Toggles normal playback
 */
function togglePlay() {
    const video = document.getElementById('outputVideo');
    if (video.paused) video.play();
    else video.pause();
}

/**
 * Moves the video by exactly one frame
 * @param {number} direction - 1 for forward, -1 for back
 */
function changeFrame(direction) {
    const video = document.getElementById('outputVideo');
    
    // Ensure video is paused during frame-by-frame stepping
    video.pause();

    // Calculate time per frame based on the metadata received from server
    const frameTime = 1 / videoFps;
    
    // Update video time
    video.currentTime += (direction * frameTime);
}

/**
 * Sync the frame counter display as the video plays
 */
document.getElementById('outputVideo').ontimeupdate = function() {
    const video = document.getElementById('outputVideo');
    const currentFrame = Math.floor(video.currentTime * videoFps);
    document.getElementById('currentFrameDisplay').innerText = `Frame: ${currentFrame}`;
};

/**
 * Utility: Converts milliseconds to formatted string
 */
function formatClockTime(ms) {
    const min = Math.floor(ms / 60000);
    const sec = Math.floor((ms % 60000) / 1000);
    const mll = Math.floor(ms % 1000);
    return `${min.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}.${mll.toString().padStart(3,'0')}`;
}

/**
 * Utility: Seeks video to specific timestamp
 */
function seekTo(ms) {
    const video = document.getElementById('outputVideo');
    video.currentTime = ms / 1000;
    video.play();
}