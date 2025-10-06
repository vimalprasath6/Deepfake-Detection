document.addEventListener("DOMContentLoaded", function () {
    console.log("🚀 Script Loaded: Deepfake Detection System Initialized!");

    const fileInput = document.getElementById("file-upload");
    const dropArea = document.getElementById("drop-area");
    const analyzeFileBtn = document.getElementById("analyze-btn-1"); // File section button
    const analyzeUrlBtn = document.getElementById("analyze-btn-2");  // Link section button
    const uploadText = dropArea?.querySelector(".upload-text");
    const urlInput = document.getElementById("url-input");

    const uploadSection = document.getElementById("upload-section");
    const linkSection = document.getElementById("link-section");
    const loadingContainer = document.querySelector(".loading-container");
    const resultContainer = document.getElementById("analysis-result");
    const resultOutput = document.getElementById("result-output");
    const progressBar = document.querySelector(".progress-bar");
    const percentageText = document.querySelector(".percentage");
    const statusText = document.querySelector(".status-text");

    if (!fileInput || !dropArea || !analyzeFileBtn || !analyzeUrlBtn || !urlInput) {
        console.error("❌ Required elements missing! Check HTML.");
        return;
    }

    // Smooth Scroll to Upload Section
    document.querySelector(".cta-button")?.addEventListener("click", () => {
        uploadSection.scrollIntoView({ behavior: "smooth" });
    });

    // Enable "Analyze Now" button only when URL is entered
    urlInput.addEventListener("input", function () {
        analyzeUrlBtn.disabled = urlInput.value.trim() === "";
    });

    // Click to Open File Dialog
    dropArea.addEventListener("click", () => fileInput.click());

    // Drag & Drop Events
    ["dragover", "dragenter"].forEach(event =>
        dropArea.addEventListener(event, e => {
            e.preventDefault();
            dropArea.classList.add("dragging");
        })
    );

    ["dragleave", "drop"].forEach(event =>
        dropArea.addEventListener(event, e => {
            e.preventDefault();
            dropArea.classList.remove("dragging");
        })
    );

    dropArea.addEventListener("drop", (e) => {
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            updateUploadText();
        }
    });

    fileInput.addEventListener("change", updateUploadText);

    function updateUploadText() {
        if (fileInput.files.length > 0) {
            uploadText.innerText = `File: ${fileInput.files[0].name}`;
        }
    }

    // Analyze File Button Click
    analyzeFileBtn.addEventListener("click", function () {
        const file = fileInput.files[0];

        if (!file) {
            alert("❌ Please upload a file before analyzing!");
            return;
        }

        toggleSections("loading");
        resetProgressBar();
        uploadAndAnalyzeFile(file);
        startLoadingAnimation();
    });

    function uploadAndAnalyzeFile(file) {
        let formData = new FormData();
        formData.append("video", file);
    
        fetch("/upload/", {
            method: "POST",
            body: formData,
            headers: { "X-CSRFToken": getCSRFToken() },
        })
        .then(handleResponse)
        .then(data => {
            if (data.file_url) {
                analyzeFile(data.file_url); // Pass the file URL to the analyze function
            } else {
                showError(new Error("❌ No file URL returned after upload."));
            }
        })
        .catch(showError);
    }
    
    function analyzeFile(fileUrl) {
        fetch("/analyze/", {
            method: "POST",
            body: JSON.stringify({ file_url: fileUrl }), // Ensure file_url is being sent
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken(),
            },
        })
        .then(handleResponse)
        .then(data => showResult(data.result))
        .catch(showError);
    }
    
    

    // Analyze URL Button Click (Link Section)
    analyzeUrlBtn.addEventListener("click", function () {
        const videoURL = urlInput.value.trim();

        if (!videoURL) {
            alert("❌ Please enter a URL before analyzing!");
            return;
        }

        console.log("📩 Sending URL to backend:", videoURL); // Debugging log

        toggleSections("loading");
        resetProgressBar();
        analyzeVideoURL(videoURL);
        startLoadingAnimation();
    });

    function analyzeVideoURL(url) {
        if (!url) {
            alert("❌ Please enter a valid video URL.");
            return;
        }
    
        console.log("📩 Sending video URL for analysis:", url); // Debugging
    
        fetch("/analyze_url/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ video_url: url }), // ✅ Use the actual URL
        })
        .then(response => response.json()) 
        .then(data => {
            console.log("🔍 Full API Response:", data); // Debugging
    
            if (data.error) {
                alert("❌ Error: " + data.error);
            } else {
                alert("✅ Analysis Result: " + (data.result || "No result"));
            }
        })
        .catch(error => {
            console.error("❌ Fetch Error:", error);
            alert("❌ Network Error: Failed to send request.");
        });
    }
    

    function handleResponse(response) {
        return response.json().then(data => {
            if (!response.ok) throw new Error(data.error || "Unknown error");
            return data;
        });
    }

    function showResult(result) {
        resultOutput.innerText = result;
        toggleSections("result");
    }

    function showError(error) {
        alert(`❌ Error: ${error.message}`);
        console.error("❌ Fetch Error:", error);
        toggleSections("upload"); // Show upload section again on failure
    }

    function toggleSections(state) {
        if (state === "loading") {
            uploadSection.style.display = "none";
            linkSection.style.display = "none";
            resultContainer.style.display = "none";
            loadingContainer.style.display = "flex";
        } else if (state === "result") {
            uploadSection.style.display = "none";
            linkSection.style.display = "none";
            loadingContainer.style.display = "none";
            resultContainer.style.display = "block";
        } else {
            uploadSection.style.display = "block";
            linkSection.style.display = "block";
            loadingContainer.style.display = "none";
            resultContainer.style.display = "none";
        }
    }

    function resetProgressBar() {
        progressBar.style.width = "0%";
        percentageText.textContent = "0%";
        statusText.textContent = "Uploading media...";
    }

    function startLoadingAnimation() {
        let progress = 0;
        percentageText.textContent = `${progress}%`;

        let interval = setInterval(() => {
            if (loadingContainer.style.display === "none") {
                clearInterval(interval);
                return;
            }

            progress = Math.min(progress + 2, 100);
            progressBar.style.width = `${progress}%`;
            percentageText.textContent = `${progress}%`;

            if (progress === 100) {
                clearInterval(interval);
                statusText.textContent = "Processing complete...";
            }
        }, 250);
    }

    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || "";
    }
});
