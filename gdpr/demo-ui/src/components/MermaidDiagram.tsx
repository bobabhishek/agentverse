'use client';

import { useEffect, useState } from 'react';
import mermaid from 'mermaid';

interface MermaidDiagramProps {
  chart: string;
}

export default function MermaidDiagram({ chart }: MermaidDiagramProps) {
  const [svg, setSvg] = useState<string>('');
  const [renderError, setRenderError] = useState<string | null>(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'base',
      themeVariables: {
        darkMode: true,
        background: '#060c1d',
        primaryColor: '#172554',
        primaryTextColor: '#ffffff',
        primaryBorderColor: '#3b82f6',
        lineColor: '#60a5fa',
        secondaryColor: '#3b0764',
        tertiaryColor: '#090f22',
        mainBkg: '#0f172a',
        nodeBorder: '#3b82f6',
        clusterBkg: '#091124',
        titleColor: '#ffffff',
        edgeLabelBackground: 'transparent',
        textColor: '#ffffff',
        fontSize: '15px',
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif'
      },
      flowchart: {
        nodeSpacing: 45,
        rankSpacing: 55,
        htmlLabels: true,
        curve: 'basis'
      }
    });

    let isMounted = true;

    const renderChart = async () => {
      try {
        setRenderError(null);
        const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        const { svg: renderedSvg } = await mermaid.render(id, chart);
        if (isMounted) {
          // Remove restrictive max-width injected by Mermaid to allow full container scaling
          const responsiveSvg = renderedSvg
            .replace(/style="max-width:\s*[^"]*"/gi, 'style="width: 100%; height: auto; min-height: 260px;"');
          setSvg(responsiveSvg);
        }
      } catch (err: unknown) {
        console.error('Mermaid render error:', err);
        if (isMounted) {
          const errMsg = err instanceof Error ? err.message : 'Diagram parsing error';
          setRenderError(errMsg);
        }
      }
    };

    renderChart();

    return () => {
      isMounted = false;
    };
  }, [chart]);

  return (
    <div className="w-full flex flex-col items-center py-2">
      <style>{`
        .mermaid-chart svg {
          width: 100% !important;
          max-width: 820px !important;
          height: auto !important;
          display: block;
          margin: 0 auto;
        }
        .mermaid-chart foreignObject {
          overflow: visible !important;
        }
        .mermaid-chart .node rect,
        .mermaid-chart .node polygon,
        .mermaid-chart .node circle,
        .mermaid-chart .node path {
          rx: 10px !important;
          ry: 10px !important;
          stroke-width: 2.5px !important;
        }
        .mermaid-chart .label,
        .mermaid-chart .node text {
          font-size: 15px !important;
          font-weight: 600 !important;
          fill: #ffffff !important;
        }
        .mermaid-chart .labelBkg {
          background-color: transparent !important;
        }
        .mermaid-chart .edgeLabel {
          background-color: transparent !important;
          padding: 0 !important;
        }
        .mermaid-chart .edgeLabel span {
          background-color: transparent !important;
          border: none !important;
          padding: 0 !important;
          color: #bfdbfe !important;
          fill: #bfdbfe !important;
          font-size: 12px !important;
          font-weight: 600 !important;
        }
        .mermaid-chart .edgeLabel p {
          background-color: #0b132b !important;
          color: #bfdbfe !important;
          fill: #bfdbfe !important;
          font-size: 12px !important;
          font-weight: 600 !important;
          border: 1px solid #1e3a8a !important;
          border-radius: 6px !important;
          padding: 2px 8px !important;
          margin: 0 !important;
          display: inline-block !important;
          line-height: 1.4 !important;
          box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5) !important;
        }
        .mermaid-chart .edgeLabel rect {
          fill: #0b132b !important;
          stroke: #1e3a8a !important;
          stroke-width: 1px !important;
          rx: 6px !important;
          ry: 6px !important;
        }
        .mermaid-chart .edgeLabel text,
        .mermaid-chart .edgeLabel tspan {
          fill: #bfdbfe !important;
          color: #bfdbfe !important;
          font-size: 12px !important;
          font-weight: 600 !important;
        }
        .mermaid-chart .flowchart-link {
          stroke: #60a5fa !important;
          stroke-width: 2.5px !important;
        }
        .mermaid-chart marker path {
          fill: #60a5fa !important;
          stroke: #60a5fa !important;
        }
      `}</style>
      {renderError ? (
        <div className="p-4 bg-rose-950/40 border border-rose-800/60 rounded-xl text-rose-300 text-xs text-center my-4">
          <p className="font-semibold mb-1">Mermaid Render Notice</p>
          <p className="font-mono text-[11px] opacity-80">{renderError}</p>
        </div>
      ) : svg ? (
        <div
          className="mermaid-chart w-full flex justify-center overflow-x-auto py-2"
          dangerouslySetInnerHTML={{ __html: svg }}
        />
      ) : (
        <div className="text-xs text-slate-500 py-10 flex items-center justify-center">
          Loading diagram...
        </div>
      )}
    </div>
  );
}
