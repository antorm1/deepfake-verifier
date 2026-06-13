const form = document.getElementById('analyzeForm');
const status = document.getElementById('status');
const result = document.getElementById('result');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  status.textContent = 'Analyzing...';
  result.textContent = '';
  const file = document.getElementById('fileInput').files[0];
  if (!file) { status.textContent = 'Choose a file first.'; return; }
  const fd = new FormData();
  fd.append('file', file);
  try {
    const res = await fetch('/api/v1/analyze', { method: 'POST', body: fd });
    const data = await res.json();
    status.textContent = '';
    result.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    status.textContent = 'Analysis failed.';
    result.textContent = String(err);
  }
});
