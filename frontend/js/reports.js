// Report Generation & Export JS
document.addEventListener("DOMContentLoaded", () => {
  const btnGeneratePdf = document.getElementById("btn-generate-pdf-report");
  const pdfDownloadContainer = document.getElementById("pdf-download-container");

  if (btnGeneratePdf) {
    btnGeneratePdf.addEventListener("click", async () => {
      const datasetId = APIClient.getActiveDatasetId();
      if (!datasetId) {
        APIClient.showToast("No active dataset selected.", "error");
        return;
      }

      APIClient.showToast("Compiling PDF Analytics Report...", "info");

      try {
        const res = await APIClient.request("/api/reports/generate", {
          method: "POST",
          body: JSON.stringify({ datasetId })
        });

        if (pdfDownloadContainer) {
          pdfDownloadContainer.innerHTML = `
            <div class="card" style="margin-top:20px; border-color:var(--accent-secondary);">
              <h3 style="color:var(--accent-secondary)">✅ PDF Report Generated!</h3>
              <p style="margin:10px 0; font-size:14px;">Your official DataLens analytics summary report is ready for download.</p>
              <a href="${res.downloadUrl}" target="_blank" class="btn btn-success" download>
                📥 Download PDF Report (${res.reportName})
              </a>
            </div>
          `;
        }

        APIClient.showToast("PDF report generated successfully!", "success");

      } catch (err) {
        console.error("Report generation error", err);
      }
    });
  }
});
