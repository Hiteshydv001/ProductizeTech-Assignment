'use strict';

const form = document.getElementById('glr-form');
const statusEl = document.getElementById('status');
const resultsSection = document.getElementById('results');
const fieldsPre = document.getElementById('fields');
const valuesPre = document.getElementById('values');
const excerptPre = document.getElementById('excerpt');
const diagnosticsLink = document.getElementById('diagnostics-link');
const submitBtn = document.getElementById('submit-btn');

// Preview elements
const docxDownloadBtn = document.getElementById('docx-download-btn');
const pdfDownloadBtn = document.getElementById('pdf-download-btn');

const pretty = (obj) => JSON.stringify(obj, null, 2);

// File input preview handlers
const templateInput = document.getElementById('template');
const reportsInput = document.getElementById('reports');
const templatePreview = document.getElementById('template-preview');
const templatePreviewIframe = document.getElementById('template-preview-iframe');
const reportsPreview = document.getElementById('reports-preview');
const reportsPreviewContainer = document.getElementById('reports-preview-container');

// Handle template file selection
if (templateInput) {
  templateInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file && templatePreview) {
      // Clear previous content
      const existingInfo = templatePreview.querySelector('.file-info');
      if (existingInfo) {
        existingInfo.remove();
      }
      
      // Create file info display
      const fileInfo = document.createElement('div');
      fileInfo.className = 'file-info';
      fileInfo.style.padding = '2rem';
      fileInfo.style.textAlign = 'center';
      fileInfo.style.background = 'white';
      fileInfo.style.border = '1px solid #ddd';
      fileInfo.style.borderRadius = '4px';
      fileInfo.innerHTML = `
        <div style="margin-bottom: 1rem;">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#2196f3" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
        </div>
        <h4 style="margin: 0 0 0.5rem 0; color: #333;">${file.name}</h4>
        <p style="margin: 0; color: #666; font-size: 0.9rem;">
          Size: ${(file.size / 1024).toFixed(2)} KB<br>
          Type: ${file.type || 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
        </p>
        <p style="margin-top: 1rem; color: #888; font-size: 0.85rem;">
          Template will be processed when you run the pipeline
        </p>
      `;
      
      if (templatePreviewIframe) {
        templatePreviewIframe.style.display = 'none';
      }
      templatePreview.appendChild(fileInfo);
      templatePreview.style.display = 'block';
    } else if (templatePreview) {
      templatePreview.style.display = 'none';
    }
  });
}

// Handle reports file selection
if (reportsInput && reportsPreviewContainer) {
  reportsInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    reportsPreviewContainer.innerHTML = '';
    
    if (files.length > 0) {
      files.forEach((file, index) => {
        const fileURL = URL.createObjectURL(file);
        
        const previewItem = document.createElement('div');
        previewItem.className = 'report-preview-item';
        
        const header = document.createElement('h5');
        header.textContent = `Report ${index + 1}: ${file.name}`;
        
        const iframe = document.createElement('iframe');
        iframe.src = fileURL;
        
        previewItem.appendChild(header);
        previewItem.appendChild(iframe);
        reportsPreviewContainer.appendChild(previewItem);
      });
      
      if (reportsPreview) {
        reportsPreview.style.display = 'block';
      }
    } else if (reportsPreview) {
      reportsPreview.style.display = 'none';
    }
  });
}

// Tab switching functionality
const tabBtns = document.querySelectorAll('.tab-btn');
if (tabBtns.length > 0) {
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.dataset.tab;
      
      // Update active tab button
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      
      // Update active preview content
      document.querySelectorAll('.preview-content').forEach(content => {
        content.classList.remove('active');
        content.style.display = 'none';
      });
      
      const targetContent = document.getElementById(`${targetTab}-preview`);
      if (targetContent) {
        targetContent.classList.add('active');
        targetContent.style.display = 'block';
      }
    });
  });
}

// Function to render PDF using PDF.js
async function renderPDF(pdfUrl, containerId) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.warn('PDF container not found:', containerId);
    return;
  }
  
  // Check if PDF.js is loaded
  if (typeof pdfjsLib === 'undefined') {
    console.error('PDF.js library not loaded');
    container.innerHTML = `
      <div style="padding: 2rem; text-align: center; color: var(--muted);">
        <p>PDF viewer not available.</p>
        <p style="font-size: 0.9rem; margin-top: 0.5rem;">Download the file to view it.</p>
      </div>
    `;
    return;
  }
  
  try {
    // Set worker source
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    
    const loadingTask = pdfjsLib.getDocument(pdfUrl + '?t=' + Date.now());
    const pdf = await loadingTask.promise;
    
    container.innerHTML = '';
    
    // Render first 3 pages
    const numPages = Math.min(pdf.numPages, 3);
    
    for (let pageNum = 1; pageNum <= numPages; pageNum++) {
      const page = await pdf.getPage(pageNum);
      const viewport = page.getViewport({ scale: 1.5 });
      
      const canvas = document.createElement('canvas');
      canvas.style.display = 'block';
      canvas.style.margin = '0 auto 1rem';
      canvas.style.border = '1px solid #d7cbb8';
      canvas.style.borderRadius = '8px';
      canvas.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
      
      const context = canvas.getContext('2d');
      canvas.height = viewport.height;
      canvas.width = viewport.width;
      
      await page.render({
        canvasContext: context,
        viewport: viewport
      }).promise;
      
      container.appendChild(canvas);
    }
    
    if (pdf.numPages > 3) {
      const morePages = document.createElement('p');
      morePages.style.textAlign = 'center';
      morePages.style.color = '#6f6659';
      morePages.style.padding = '1rem';
      morePages.textContent = `... and ${pdf.numPages - 3} more page(s). Download to view all.`;
      container.appendChild(morePages);
    }
  } catch (error) {
    console.error('PDF rendering error:', error);
    container.innerHTML = `
      <div style="padding: 2rem; text-align: center; color: #6f6659;">
        <p>Unable to preview PDF in browser.</p>
        <p style="font-size: 0.9rem; margin-top: 0.5rem;">Download the file to view it.</p>
      </div>
    `;
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const templateFile = document.getElementById('template').files[0];
  const reportFiles = Array.from(document.getElementById('reports').files);

  if (!templateFile) {
    statusEl.textContent = 'Please select a .docx template.';
    return;
  }

  if (reportFiles.length === 0) {
    statusEl.textContent = 'Please add at least one PDF report.';
    return;
  }

  const formData = new FormData();
  formData.append('template', templateFile);
  reportFiles.forEach((file) => formData.append('reports', file));

  statusEl.textContent = 'Running pipeline. This can take ~30s depending on the LLM.';
  submitBtn.disabled = true;
  resultsSection.hidden = true;

  try {
    const response = await fetch('/api/glr', {
      method: 'POST',
      body: formData,
    });

    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.detail || 'Pipeline failed');
    }

    // Verify all required elements exist
    if (!fieldsPre || !valuesPre || !excerptPre) {
      console.error('Missing result display elements');
      throw new Error('UI elements not found');
    }

    fieldsPre.textContent = pretty(payload.extracted_fields);
    valuesPre.textContent = pretty(payload.filled_values);
    excerptPre.textContent = payload.report_excerpt;
    
    // Setup download links
    const docxFilename = `filled_template_${payload.run_id}.docx`;
    const pdfFilename = `filled_template_${payload.run_id}.pdf`;
    
    if (docxDownloadBtn) {
      docxDownloadBtn.href = payload.download_url;
      docxDownloadBtn.setAttribute('download', docxFilename);
    }
    
    const docxFilenameSpan = document.getElementById('docx-filename');
    if (docxFilenameSpan) {
      docxFilenameSpan.textContent = docxFilename;
    }
    
    if (payload.pdf_url && pdfDownloadBtn) {
      pdfDownloadBtn.href = payload.pdf_url;
      pdfDownloadBtn.setAttribute('download', pdfFilename);
      pdfDownloadBtn.style.display = 'inline-block';
      
      // Render PDF preview
      setTimeout(() => {
        renderPDF(payload.pdf_url, 'pdf-viewer-container');
      }, 100);
      
      // Make sure PDF tab is active
      const pdfPreview = document.getElementById('pdf-preview');
      const docxPreview = document.getElementById('docx-preview');
      
      document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.dataset.tab === 'pdf') {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
      
      if (pdfPreview) {
        pdfPreview.classList.add('active');
        pdfPreview.style.display = 'block';
      }
      if (docxPreview) {
        docxPreview.classList.remove('active');
        docxPreview.style.display = 'none';
      }
    } else {
      if (pdfDownloadBtn) {
        pdfDownloadBtn.style.display = 'none';
      }
      // Show DOCX tab if no PDF
      const pdfPreview = document.getElementById('pdf-preview');
      const docxPreview = document.getElementById('docx-preview');
      
      document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.dataset.tab === 'docx') {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
      
      if (pdfPreview) {
        pdfPreview.classList.remove('active');
        pdfPreview.style.display = 'none';
      }
      if (docxPreview) {
        docxPreview.classList.add('active');
        docxPreview.style.display = 'block';
      }
    }
    
    if (diagnosticsLink) {
      diagnosticsLink.href = payload.diagnostics_url;
    }

    resultsSection.hidden = false;
    statusEl.textContent = 'Success! Review the extracted values below.';
  } catch (error) {
    console.error(error);
    statusEl.textContent = error.message;
  } finally {
    submitBtn.disabled = false;
  }
});
