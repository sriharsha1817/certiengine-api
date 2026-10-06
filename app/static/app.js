let recipientRowCounter = 0;
let activePollingJobs = new Set();

document.addEventListener('DOMContentLoaded', () => {
  addRecipientRow('Alice Smith', 'alice@example.com', '{"role": "Participant", "grade": "Distinction"}');
  addRecipientRow('Bob Johnson', 'bob@example.com', '{"role": "Participant"}');
  addRecipientRow('Charlie (Invalid Email Test)', 'charlie_invalid_email', '{"role": "Speaker"}');
  fetchJobs();
});

function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
  
  const targetBtn = Array.from(document.querySelectorAll('.tab-btn')).find(btn => btn.getAttribute('onclick').includes(tabId));
  if (targetBtn) targetBtn.classList.add('active');
  
  const targetContent = document.getElementById(tabId);
  if (targetContent) targetContent.classList.add('active');

  if (tabId === 'tab-jobs') fetchJobs();
}

function addRecipientRow(name = '', email = '', attrs = '') {
  recipientRowCounter++;
  const tbody = document.getElementById('recipients-tbody');
  const tr = document.createElement('tr');
  tr.id = `recipient-row-${recipientRowCounter}`;
  
  tr.innerHTML = `
    <td>${recipientRowCounter}</td>
    <td><input type="text" class="r-name" value="${name}" placeholder="Recipient Name" required style="width: 100%;"></td>
    <td><input type="text" class="r-email" value="${email}" placeholder="email@domain.com" required style="width: 100%;"></td>
    <td><input type="text" class="r-attrs" value="${attrs}" placeholder='{"score": "98%"}' style="width: 100%;"></td>
    <td>
      <button type="button" class="btn btn-danger btn-sm" onclick="removeRecipientRow('${tr.id}')">&times; Remove</button>
    </td>
  `;
  tbody.appendChild(tr);
  updateRecipientCount();
}

function removeRecipientRow(rowId) {
  const row = document.getElementById(rowId);
  if (row) row.remove();
  updateRecipientCount();
}

function updateRecipientCount() {
  const count = document.querySelectorAll('#recipients-tbody tr').length;
  document.getElementById('recipient-count').innerText = count;
}

function loadDemoData() {
  document.getElementById('recipients-tbody').innerHTML = '';
  recipientRowCounter = 0;
  addRecipientRow('Elena Rostova', 'elena.rostova@tech.edu', '{"grade": "A+", "score": "98/100"}');
  addRecipientRow('Marcus Vance', 'marcus.vance@company.io', '{"role": "Keynote Speaker"}');
  addRecipientRow('Sophia Loren', 'sophia@domain.org', '{"distinction": "Honors"}');
  addRecipientRow('David Invalid Email', 'david_not_an_email', '{"note": "Intentional failure test"}');
}

async function handleCreateJob(event) {
  event.preventDefault();
  
  const rows = document.querySelectorAll('#recipients-tbody tr');
  if (rows.length === 0) {
    alert("Please add at least one recipient.");
    return;
  }

  const recipients = [];
  let parseError = false;

  rows.forEach(row => {
    const name = row.querySelector('.r-name').value.trim();
    const email = row.querySelector('.r-email').value.trim();
    const attrsStr = row.querySelector('.r-attrs').value.trim();

    let custom_attributes = null;
    if (attrsStr) {
      try {
        custom_attributes = JSON.parse(attrsStr);
      } catch (err) {
        custom_attributes = { raw_info: attrsStr };
      }
    }

    if (name && email) {
      recipients.push({ name, email, custom_attributes });
    }
  });

  const payload = {
    event_name: document.getElementById('event_name').value,
    issuer_name: document.getElementById('issuer_name').value,
    issuer_title: document.getElementById('issuer_title').value,
    template_style: document.getElementById('template_style').value,
    issue_date: document.getElementById('issue_date').value || null,
    recipients: recipients
  };

  const asyncMode = document.getElementById('async_process').value === 'true';

  try {
    const response = await fetch(`/api/v1/jobs?async_process=${asyncMode}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errData = await response.json();
      alert(`Job Creation Failed: ${errData.detail || JSON.stringify(errData)}`);
      return;
    }

    const job = await response.json();
    alert(`Generation Job #${job.id.substring(0, 8)} successfully submitted!`);
    switchTab('tab-jobs');
    if (asyncMode) pollJob(job.id);
  } catch (err) {
    alert(`Error submitting job: ${err.message}`);
  }
}

async function handleCSVUpload(event) {
  event.preventDefault();
  const fileInput = document.getElementById('csv_file');
  if (!fileInput.files[0]) {
    alert("Please select a CSV file.");
    return;
  }

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('event_name', document.getElementById('csv_event_name').value);
  formData.append('issuer_name', document.getElementById('csv_issuer_name').value);
  formData.append('template_style', document.getElementById('csv_template_style').value);

  try {
    const response = await fetch('/api/v1/jobs/upload-csv', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errData = await response.json();
      alert(`CSV Upload Failed: ${errData.detail}`);
      return;
    }

    const job = await response.json();
    alert(`CSV Bulk Job #${job.id.substring(0, 8)} created successfully!`);
    switchTab('tab-jobs');
    pollJob(job.id);
  } catch (err) {
    alert(`Error uploading CSV: ${err.message}`);
  }
}

async function fetchJobs() {
  try {
    const res = await fetch('/api/v1/jobs');
    if (!res.ok) return;
    const jobs = await res.json();
    
    document.getElementById('jobs-count-badge').innerText = jobs.length;
    document.getElementById('stat-total-jobs').innerText = jobs.length;
    
    let totalCerts = 0;
    let totalSuccess = 0;

    const tbody = document.getElementById('jobs-list-tbody');
    if (jobs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #9ca3af;">No jobs submitted yet.</td></tr>';
      return;
    }

    tbody.innerHTML = jobs.map(job => {
      totalCerts += job.total_count;
      totalSuccess += job.success_count;

      if (['PENDING', 'PROCESSING'].includes(job.status)) {
        pollJob(job.id);
      }

      return `
        <tr>
          <td><code>${job.id.substring(0, 8)}...</code></td>
          <td><strong>${job.event_name}</strong></td>
          <td><span class="status-badge status-${job.status}">${job.status}</span></td>
          <td>
            <div style="font-size: 0.8rem; margin-bottom: 2px;">${job.progress_percentage}%</div>
            <div class="progress-container">
              <div class="progress-bar" style="width: ${job.progress_percentage}%;"></div>
            </div>
          </td>
          <td>
            <span style="color: #34d399;">✓ ${job.success_count}</span> / 
            <span style="color: #f87171;">✗ ${job.failed_count}</span> / 
            <strong>${job.total_count}</strong>
          </td>
          <td>${new Date(job.created_at).toLocaleTimeString()}</td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="viewJobDetails('${job.id}')">👁️ Details</button>
            <a class="btn btn-secondary btn-sm" href="/api/v1/jobs/${job.id}/download-all?format=pdf" target="_blank">📦 ZIP</a>
          </td>
        </tr>
      `;
    }).join('');

    document.getElementById('stat-total-certs').innerText = totalSuccess;
    const rate = totalCerts > 0 ? Math.round((totalSuccess / totalCerts) * 100) : 100;
    document.getElementById('stat-success-rate').innerText = `${rate}%`;

  } catch (err) {
    console.error("Error fetching jobs:", err);
  }
}

function pollJob(jobId) {
  if (activePollingJobs.has(jobId)) return;
  activePollingJobs.add(jobId);

  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/api/v1/jobs/${jobId}`);
      if (res.ok) {
        const job = await res.json();
        fetchJobs(); // Update table
        if (['COMPLETED', 'FAILED', 'PARTIALLY_FAILED'].includes(job.status)) {
          clearInterval(interval);
          activePollingJobs.delete(jobId);
        }
      }
    } catch (err) {
      clearInterval(interval);
      activePollingJobs.delete(jobId);
    }
  }, 1500);
}

async function viewJobDetails(jobId) {
  try {
    const res = await fetch(`/api/v1/jobs/${jobId}`);
    if (!res.ok) return;
    const job = await res.json();

    const body = document.getElementById('modal-body');
    body.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem;">
        <div>
          <h2>Job #${job.id}</h2>
          <p style="color: #9ca3af;">Event: <strong>${job.event_name}</strong> | Issuer: ${job.issuer_name}</p>
        </div>
        <span class="status-badge status-${job.status}">${job.status}</span>
      </div>

      <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem; background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 0.5rem;">
        <div>Total: <strong>${job.total_count}</strong></div>
        <div style="color: #34d399;">Success: <strong>${job.success_count}</strong></div>
        <div style="color: #f87171;">Failed: <strong>${job.failed_count}</strong></div>
        <div style="margin-left: auto;">
          <a class="btn btn-primary btn-sm" href="/api/v1/jobs/${job.id}/download-all?format=pdf" target="_blank">📦 Download All Certificates (ZIP)</a>
        </div>
      </div>

      <h3>Recipients & Certificates</h3>
      <div class="table-responsive" style="margin-top: 1rem;">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Status</th>
              <th>Certificate ID / Error</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${job.recipients.map(r => `
              <tr>
                <td><strong>${r.recipient_name}</strong></td>
                <td>${r.recipient_email}</td>
                <td><span class="status-badge status-${r.status}">${r.status}</span></td>
                <td>
                  ${r.status === 'SUCCESS' 
                    ? `<code>${r.id.substring(0, 12)}...</code>` 
                    : `<span style="color: #f87171; font-size: 0.85rem;">${r.error_message || 'Failed'}</span>`}
                </td>
                <td>
                  ${r.status === 'SUCCESS' ? `
                    <button class="btn btn-secondary btn-sm" onclick="viewCertificatePreview('${r.id}')">🖼️ Preview</button>
                    <a class="btn btn-primary btn-sm" href="${r.pdf_download_url}" target="_blank">📄 PDF</a>
                    <a class="btn btn-secondary btn-sm" href="${r.png_download_url}" target="_blank">🖼️ PNG</a>
                  ` : '—'}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('modal-overlay').style.display = 'flex';
  } catch (err) {
    alert("Error loading job details: " + err.message);
  }
}

async function viewCertificatePreview(certId) {
  try {
    const res = await fetch(`/api/v1/certificates/${certId}`);
    if (!res.ok) return;
    const cert = await res.json();

    const body = document.getElementById('modal-body');
    body.innerHTML = `
      <h2 style="margin-bottom: 0.5rem;">Certificate Preview</h2>
      <p style="color: #9ca3af; margin-bottom: 1rem;">Recipient: <strong>${cert.recipient_name}</strong> (${cert.recipient_email})</p>

      <img src="${cert.png_download_url}" alt="Certificate Preview" class="certificate-preview-img">

      <div style="display: flex; gap: 1rem; justify-content: flex-end;">
        <a class="btn btn-secondary" href="${cert.png_download_url}" target="_blank">Download High-Res PNG</a>
        <a class="btn btn-primary" href="${cert.pdf_download_url}" target="_blank">Download Vector PDF</a>
        <a class="btn btn-secondary" href="${cert.verification_url}" target="_blank">Verify Seal Page</a>
      </div>
    `;

    document.getElementById('modal-overlay').style.display = 'flex';
  } catch (err) {
    alert("Error previewing certificate: " + err.message);
  }
}

function closeModal() {
  document.getElementById('modal-overlay').style.display = 'none';
}

async function handleVerify(event) {
  event.preventDefault();
  const certId = document.getElementById('verify_id').value.trim();
  if (!certId) return;

  try {
    const res = await fetch(`/api/v1/certificates/verify/${certId}`);
    const data = await res.json();

    const container = document.getElementById('verify-result');
    container.style.display = 'block';

    if (data.is_valid) {
      container.style.background = 'rgba(16, 185, 129, 0.15)';
      container.style.border = '1px solid rgba(16, 185, 129, 0.3)';
      container.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.75rem; font-size: 1.25rem; font-weight: 700; color: #34d399; margin-bottom: 1rem;">
          <span>✅</span> Official Authentic Certificate
        </div>
        <div style="grid-template-columns: repeat(2, 1fr); display: grid; gap: 0.75rem; font-size: 0.95rem;">
          <div>Recipient Name: <strong>${data.recipient_name}</strong></div>
          <div>Recipient Email: <strong>${data.recipient_email}</strong></div>
          <div>Course/Event: <strong>${data.event_name}</strong></div>
          <div>Issuing Authority: <strong>${data.issuer_name}</strong></div>
          <div>Issue Date: <strong>${data.issue_date || 'N/A'}</strong></div>
          <div>SHA-256 Hash: <code>${data.verification_hash || 'N/A'}</code></div>
        </div>
      `;
    } else {
      container.style.background = 'rgba(244, 63, 94, 0.15)';
      container.style.border = '1px solid rgba(244, 63, 94, 0.3)';
      container.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.75rem; font-size: 1.25rem; font-weight: 700; color: #f87171;">
          <span>❌</span> Invalid Certificate
        </div>
        <p style="margin-top: 0.5rem; color: #fda4af;">No valid authentic certificate found for ID: <code>${certId}</code> (Status: ${data.status})</p>
      `;
    }
  } catch (err) {
    alert("Error verifying certificate: " + err.message);
  }
}
