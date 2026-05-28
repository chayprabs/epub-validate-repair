"use client";

import dynamic from "next/dynamic";

const ValidationWorkbench = dynamic(
  () => import("./validation-workbench").then((module) => module.ValidationWorkbench),
  {
    ssr: false,
    loading: () => (
      <section className="panel workbench">
        <div className="workbench-header">
          <div>
            <p className="eyebrow">Workbench</p>
            <h2>Loading the validation and repair surface...</h2>
          </div>
          <div className="badge subtle">Preparing the worker connection</div>
        </div>
      </section>
    )
  }
);

export function WorkbenchShell() {
  return <ValidationWorkbench />;
}
