document.getElementById("fetch").addEventListener("click", async () => {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    const url = tab.url;
    const out = document.getElementById("output");
    try {
      const res = await fetch("http://localhost:8000/scrape", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({url})
      });
      const data = await res.json();
      out.textContent= JSON.stringify(data, null, 2);
    } catch(e) {
      out.textContent = "Error: " + e.message;
    }
  });
  