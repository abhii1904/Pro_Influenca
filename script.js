async function getHashtags() {
  const query = document.getElementById("topicInput").value;

  if (!query) {
    alert("Please enter a topic!");
    return;
  }

  try {
    const response = await fetch(`http://127.0.0.1:5000/api/hashtags?query=${encodeURIComponent(query)}`);
    const data = await response.json();

    const resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = "";

    if (data.error) {
      resultsDiv.innerHTML = `<p style="color:red">${data.error}</p>`;
    } else {
      data.hashtags.forEach(tag => {
        const span = document.createElement("span");
        span.textContent = tag;
        span.style.padding = "6px 10px";
        span.style.margin = "5px";
        span.style.background = "#e5e7eb";
        span.style.borderRadius = "20px";
        resultsDiv.appendChild(span);
      });
    }
  } catch (err) {
    console.error("Error fetching hashtags:", err);
    document.getElementById("results").innerHTML = `<p style="color:red">Failed to fetch hashtags.</p>`;
  }
}
