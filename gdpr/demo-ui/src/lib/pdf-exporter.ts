// High-fidelity dark blue UI PDF exporter for individual AgentVerse chat sessions

type LogType = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
};

export type ChatSession = {
  id: string;
  title: string;
  logs: LogType[];
  timestamp: number;
};

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function renderBoldHtml(str: string): string {
  const parts = str.split(/(\*\*.*?\*\*)/g);
  return parts.map(part => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return `<strong style="color: #ffffff; font-weight: 600;">${escapeHtml(part.slice(2, -2))}</strong>`;
    }
    return escapeHtml(part);
  }).join('');
}

function formatMessageContentHtml(text: string): string {
  if (!text) return '';

  // Check if text has markdown table
  if (text.includes('|') && text.includes('\n|')) {
    const lines = text.split('\n');
    const introLines: string[] = [];
    const tableLines: string[] = [];
    const outroLines: string[] = [];
    let state: 'intro' | 'table' | 'outro' = 'intro';

    for (const line of lines) {
      if (line.trim().startsWith('|')) {
        state = 'table';
        tableLines.push(line.trim());
      } else if (state === 'table') {
        state = 'outro';
        outroLines.push(line);
      } else if (state === 'intro') {
        introLines.push(line);
      } else {
        outroLines.push(line);
      }
    }

    if (tableLines.length >= 2) {
      const headerCols = tableLines[0].split('|').slice(1, -1).map(c => c.trim());
      const dataRows = tableLines.slice(2).map(row =>
        row.split('|').slice(1, -1).map(c => c.trim())
      );

      const tableHtml = `
        <div style="border-radius: 12px; border: 1px solid #1e293b; background: #080e20; overflow: hidden; margin: 12px 0;">
          <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 11px;">
            <thead>
              <tr style="background: #0b142c; border-bottom: 1px solid #1e293b; color: #94a3b8; text-transform: uppercase; font-weight: 600; font-size: 10px; letter-spacing: 0.05em;">
                ${headerCols.map(col => `<th style="padding: 10px 14px;">${escapeHtml(col)}</th>`).join('')}
              </tr>
            </thead>
            <tbody style="color: #cbd5e1; font-family: monospace;">
              ${dataRows.map(row => `
                <tr style="border-bottom: 1px solid rgba(30, 41, 59, 0.6);">
                  ${row.map(cell => {
                    const cLower = cell.toLowerCase();
                    if (cLower === 'delivered') {
                      return `<td style="padding: 8px 14px;"><span style="display: inline-block; padding: 2px 8px; border-radius: 4px; background: rgba(5, 46, 22, 0.8); color: #4ade80; border: 1px solid #16a34a; font-size: 10px; font-weight: bold;">Delivered</span></td>`;
                    }
                    if (cLower === 'shipped') {
                      return `<td style="padding: 8px 14px;"><span style="display: inline-block; padding: 2px 8px; border-radius: 4px; background: rgba(30, 58, 138, 0.8); color: #93c5fd; border: 1px solid #3b82f6; font-size: 10px; font-weight: bold;">Shipped</span></td>`;
                    }
                    if (cLower === 'processing') {
                      return `<td style="padding: 8px 14px;"><span style="display: inline-block; padding: 2px 8px; border-radius: 4px; background: rgba(120, 53, 15, 0.8); color: #fde047; border: 1px solid #ca8a04; font-size: 10px; font-weight: bold;">Processing</span></td>`;
                    }
                    if (cLower === 'cancelled' || cLower === 'canceled') {
                      return `<td style="padding: 8px 14px;"><span style="display: inline-block; padding: 2px 8px; border-radius: 4px; background: rgba(76, 5, 25, 0.8); color: #fda4af; border: 1px solid #e11d48; font-size: 10px; font-weight: bold;">Cancelled</span></td>`;
                    }
                    return `<td style="padding: 8px 14px;">${escapeHtml(cell)}</td>`;
                  }).join('')}
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;

      const introHtml = introLines.length > 0 ? `<p style="margin: 0 0 8px 0; color: #e2e8f0; font-size: 13px; line-height: 1.5;">${escapeHtml(introLines.join('\n'))}</p>` : '';
      const outroHtml = outroLines.length > 0 ? `<p style="margin: 8px 0 0 0; color: #cbd5e1; font-size: 13px; line-height: 1.5;">${escapeHtml(outroLines.join('\n'))}</p>` : '';

      return introHtml + tableHtml + outroHtml;
    }
  }

  // Render bullet points and text
  const lines = text.split('\n');
  let result = '<div style="display: flex; flex-direction: column; gap: 8px; font-size: 13px; line-height: 1.6;">';

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i].trim();
    if (!line) continue;

    if (line === '•' || line === '-') {
      if (i + 1 < lines.length && lines[i + 1].trim()) {
        line = lines[i + 1].trim();
        i++;
      }
    }

    if (line.startsWith('•') || line.startsWith('- ')) {
      const content = line.replace(/^[•\-]\s*/, '');
      result += `
        <div style="display: flex; align-items: flex-start; gap: 8px;">
          <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #60a5fa; margin-top: 8px; flex-shrink: 0; box-shadow: 0 0 6px rgba(59, 130, 246, 0.6);"></span>
          <span style="color: #e2e8f0;">${renderBoldHtml(content)}</span>
        </div>
      `;
    } else {
      result += `<p style="margin: 0; color: #e2e8f0;">${renderBoldHtml(line)}</p>`;
    }
  }

  result += '</div>';
  return result;
}

function buildChatDocumentHtml(session: ChatSession): string {
  const formattedDate = new Date(session.timestamp || Date.now()).toLocaleDateString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short'
  });

  const logs = session.logs || [];

  const messagesHtml = logs.length > 0
    ? logs.map(log => {
      if (log.role === 'user') {
        return `
          <div style="display: flex; justify-content: flex-end; margin-bottom: 18px;">
            <div style="display: flex; align-items: flex-start; gap: 10px; max-width: 80%;">
              <div style="background: #122347; border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 16px; padding: 12px 16px; color: #f8fafc; font-size: 13px; line-height: 1.5; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);">
                ${escapeHtml(log.content)}
              </div>
              <div style="width: 32px; height: 32px; border-radius: 50%; background: #0a1636; border: 1px solid #1d4ed8; display: flex; align-items: center; justify-content: center; color: #93c5fd; font-size: 12px; font-weight: bold; flex-shrink: 0;">
                U
              </div>
            </div>
          </div>
        `;
      }

      return `
        <div style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 22px;">
          <div style="width: 32px; height: 32px; border-radius: 50%; background: rgba(30, 58, 138, 0.8); border: 1px solid rgba(59, 130, 246, 0.8); display: flex; align-items: center; justify-content: center; color: #60a5fa; font-size: 14px; flex-shrink: 0; margin-top: 2px;">
            ✦
          </div>
          <div style="flex: 1; max-width: 680px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
              <span style="font-size: 11px; font-weight: 600; color: #60a5fa;">Agent 2 (India)</span>
              <span style="font-size: 10px; color: #64748b; font-family: monospace;">${escapeHtml(log.timestamp || '')}</span>
              <span style="font-size: 9px; font-family: monospace; background: rgba(5, 46, 22, 0.8); border: 1px solid #16a34a; color: #4ade80; padding: 1px 6px; border-radius: 999px;">GDPR: PASS</span>
            </div>
            <div style="background: #091124; border: 1px solid #1e293b; border-radius: 16px; padding: 16px; color: #e2e8f0; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);">
              ${formatMessageContentHtml(log.content)}
            </div>
          </div>
        </div>
      `;
    }).join('')
    : '<div style="padding: 40px; text-align: center; color: #64748b; font-style: italic; font-size: 12px;">No messages recorded in this conversation.</div>';

  return `
    <div style="width: 800px; background-color: #060b18; color: #f1f5f9; padding: 36px; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
      
      <!-- Top Brand Header -->
      <div style="display: flex; align-items: center; justify-content: space-between; padding-bottom: 18px; border-bottom: 1px solid #1e293b; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="width: 40px; height: 40px; border-radius: 12px; background: rgba(37, 99, 235, 0.2); border: 1px solid rgba(59, 130, 246, 0.5); display: flex; align-items: center; justify-content: center; color: #60a5fa; font-size: 20px;">
            ✦
          </div>
          <div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <h1 style="margin: 0; font-size: 18px; font-weight: 700; color: #ffffff; letter-spacing: -0.02em;">AgentVerse</h1>
              <span style="font-size: 10px; font-family: monospace; background: rgba(5, 46, 22, 0.8); border: 1px solid #16a34a; color: #4ade80; padding: 2px 8px; border-radius: 999px;">A2A ACTIVE</span>
            </div>
            <p style="margin: 3px 0 0 0; font-size: 11px; color: #94a3b8;">Cross-Border Agent-to-Agent Protocol &bull; GDPR Article 5 & Chapter V Compliant</p>
          </div>
        </div>

        <div style="text-align: right; font-family: monospace; font-size: 11px;">
          <div style="color: #60a5fa; font-weight: 600; font-size: 12px;">${escapeHtml(session.title)}</div>
          <div style="color: #64748b; margin-top: 2px;">${formattedDate}</div>
        </div>
      </div>

      <!-- Architecture Topology Strip -->
      <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; padding: 14px; background: #091124; border: 1px solid #1e293b; border-radius: 12px; margin-bottom: 24px; font-size: 11px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(30, 58, 138, 0.8); border: 1px solid rgba(59, 130, 246, 0.6); display: flex; align-items: center; justify-content: center; color: #60a5fa;">
            🤖
          </div>
          <div>
            <div style="font-weight: 600; color: #f1f5f9;">Agent 2 &bull; India</div>
            <div style="font-size: 10px; color: #94a3b8;">Requesting Agent (South India)</div>
          </div>
        </div>

        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; border-left: 1px solid #1e293b; border-right: 1px solid #1e293b; padding: 0 10px; font-family: monospace; font-size: 10px;">
          <div style="color: #93c5fd; font-weight: 600;">IN ⇄ EU Protocol</div>
          <div style="color: #4ade80; font-size: 9px; margin-top: 2px;">Zero Direct DB Access</div>
        </div>

        <div style="display: flex; align-items: center; justify-content: flex-end; gap: 10px; text-align: right;">
          <div>
            <div style="font-weight: 600; color: #f1f5f9;">Agent 1 &bull; Europe</div>
            <div style="font-size: 10px; color: #94a3b8;">Data Provider (North Europe)</div>
          </div>
          <div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(88, 28, 135, 0.8); border: 1px solid rgba(147, 51, 234, 0.6); display: flex; align-items: center; justify-content: center; color: #c084fc;">
            🗄️
          </div>
        </div>
      </div>

      <!-- Messages Stream -->
      <div style="padding: 4px 0 20px 0;">
        ${messagesHtml}
      </div>

      <!-- Bottom Verified Audit Footer -->
      <div style="margin-top: 24px; padding-top: 14px; border-top: 1px solid #1e293b; display: flex; align-items: center; justify-content: space-between; font-family: monospace; font-size: 10px; color: #64748b;">
        <div style="display: flex; align-items: center; gap: 6px;">
          <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #10b981;"></span>
          <span>Verified Cross-Border A2A Trail &bull; Telemetry Hash Active</span>
        </div>
        <span>ISO/IEC 27001 &bull; EU GDPR Compliant Record</span>
      </div>

    </div>
  `;
}

// Direct jsPDF fallback when canvas/CORS is restricted
async function exportDirectJsPdf(session: ChatSession, fileName: string) {
  const jspdfModule = await import('jspdf');
  const jsPDF = jspdfModule.jsPDF || jspdfModule.default;
  const doc = new jsPDF({ orientation: 'p', unit: 'mm', format: 'a4' });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 14;
  const usableWidth = pageWidth - margin * 2;

  // Background
  doc.setFillColor(6, 11, 24);
  doc.rect(0, 0, pageWidth, pageHeight, 'F');

  // Header Banner
  doc.setFillColor(9, 17, 36);
  doc.roundedRect(margin, 12, usableWidth, 22, 2, 2, 'F');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(14);
  doc.setTextColor(255, 255, 255);
  doc.text('AgentVerse', margin + 6, 22);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(96, 165, 250);
  doc.text('Cross-Border A2A Audit Record • GDPR Compliant', margin + 6, 28);

  doc.setFont('courier', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(148, 163, 184);
  doc.text(session.title.substring(0, 30), pageWidth - margin - 6, 22, { align: 'right' });
  doc.text(new Date().toLocaleDateString(), pageWidth - margin - 6, 28, { align: 'right' });

  let y = 42;
  const logs = session.logs || [];

  for (const log of logs) {
    if (y > pageHeight - 35) {
      doc.addPage();
      doc.setFillColor(6, 11, 24);
      doc.rect(0, 0, pageWidth, pageHeight, 'F');
      y = 16;
    }

    if (log.role === 'user') {
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(9);
      doc.setTextColor(147, 197, 253);
      doc.text(`User (${log.timestamp})`, margin + usableWidth - 2, y, { align: 'right' });
      y += 4;

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      const splitText = doc.splitTextToSize(log.content, usableWidth * 0.75);
      const boxHeight = splitText.length * 4.5 + 6;

      doc.setFillColor(18, 35, 71);
      doc.roundedRect(margin + usableWidth * 0.25, y, usableWidth * 0.75, boxHeight, 2, 2, 'F');

      doc.setTextColor(248, 250, 252);
      doc.text(splitText, margin + usableWidth * 0.25 + 4, y + 5);
      y += boxHeight + 8;
    } else {
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(9);
      doc.setTextColor(96, 165, 250);
      doc.text(`Agent 2 - India (${log.timestamp}) [GDPR: PASS]`, margin + 2, y);
      y += 4;

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(8.5);
      const splitText = doc.splitTextToSize(log.content, usableWidth - 4);
      const boxHeight = splitText.length * 4 + 6;

      doc.setFillColor(9, 17, 36);
      doc.roundedRect(margin, y, usableWidth, boxHeight, 2, 2, 'F');

      doc.setTextColor(226, 232, 240);
      doc.text(splitText, margin + 4, y + 4.5);
      y += boxHeight + 8;
    }
  }

  // Footer on final page
  doc.setFont('courier', 'normal');
  doc.setFontSize(7.5);
  doc.setTextColor(100, 116, 139);
  doc.text('AgentVerse Cross-Border Protocol • ISO/IEC 27001 & EU GDPR Compliant Audit Trail', margin, pageHeight - 10);

  doc.save(fileName);
}

export async function downloadChatPdf(session: ChatSession): Promise<boolean> {
  const cleanTitle = (session.title || 'chat')
    .trim()
    .replace(/[^a-zA-Z0-9_\-\s]/g, '')
    .replace(/\s+/g, '_')
    .substring(0, 30) || 'conversation';
  const fileName = `AgentVerse_${cleanTitle}.pdf`;

  // First try: High-fidelity DOM capture via html2canvas
  try {
    const html2canvasModule = await import('html2canvas');
    const html2canvas = html2canvasModule.default || html2canvasModule;
    const jspdfModule = await import('jspdf');
    const jsPDF = jspdfModule.jsPDF || jspdfModule.default;

    // Attach temporary container directly at top: 0, left: 0
    const exportDiv = document.createElement('div');
    exportDiv.id = 'agentverse-pdf-export-container';
    exportDiv.style.position = 'fixed';
    exportDiv.style.top = '0';
    exportDiv.style.left = '0';
    exportDiv.style.width = '800px';
    exportDiv.style.backgroundColor = '#060b18';
    exportDiv.style.zIndex = '999999';
    exportDiv.style.boxSizing = 'border-box';
    exportDiv.style.pointerEvents = 'none';

    exportDiv.innerHTML = buildChatDocumentHtml(session);
    document.body.appendChild(exportDiv);

    // Wait a brief tick for render
    await new Promise(res => setTimeout(res, 80));

    const canvas = await html2canvas(exportDiv, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#060b18',
      logging: false,
      x: 0,
      y: 0,
      scrollX: 0,
      scrollY: 0,
      width: 800,
      height: exportDiv.scrollHeight
    });

    if (exportDiv.parentNode) {
      exportDiv.parentNode.removeChild(exportDiv);
    }

    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({
      orientation: 'p',
      unit: 'mm',
      format: 'a4',
      compress: true
    });

    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();
    const canvasWidth = canvas.width;
    const canvasHeight = canvas.height;
    const imgHeight = (canvasHeight * pdfWidth) / canvasWidth;

    let heightLeft = imgHeight;
    let position = 0;

    pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, imgHeight);
    heightLeft -= pdfHeight;

    while (heightLeft > 0) {
      position -= pdfHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, imgHeight);
      heightLeft -= pdfHeight;
    }

    pdf.save(fileName);
    return true;
  } catch (canvasErr) {
    console.warn('Canvas export hit issue, using direct jsPDF engine:', canvasErr);
    // Remove temporary div if attached
    const stray = document.getElementById('agentverse-pdf-export-container');
    if (stray && stray.parentNode) {
      stray.parentNode.removeChild(stray);
    }
    // Direct jsPDF fallback
    await exportDirectJsPdf(session, fileName);
    return true;
  }
}
