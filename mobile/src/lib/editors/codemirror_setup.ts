/**
 * CodeMirror 6 setup — shared builder for YAML / Markdown / JSON / JS editors.
 *
 * Lazy-loaded from the M13+ editor components so the authoring chunk stays
 * out of the main bundle. Dark theme matches the app.
 */

import { defaultKeymap, history, historyKeymap } from "@codemirror/commands";
import { bracketMatching, foldGutter, indentOnInput } from "@codemirror/language";
import { javascript } from "@codemirror/lang-javascript";
import { json } from "@codemirror/lang-json";
import { markdown } from "@codemirror/lang-markdown";
import { yaml } from "@codemirror/lang-yaml";
import { lintGutter, linter, type Diagnostic } from "@codemirror/lint";
import { EditorState, Compartment, type Extension } from "@codemirror/state";
import {
  EditorView,
  highlightActiveLine,
  keymap,
  lineNumbers,
} from "@codemirror/view";

export type EditorLang = "yaml" | "markdown" | "json" | "javascript";

export interface CreateEditorOptions {
  doc: string;
  lang: EditorLang;
  onChange?: (doc: string) => void;
  onBlur?: (doc: string) => void;
  lint?: (doc: string) => Diagnostic[] | Promise<Diagnostic[]>;
  /** Force line-wrapping (mandatory on mobile). */
  wrapping?: boolean;
}

const darkTheme = EditorView.theme(
  {
    "&": {
      color: "#e6e8ec",
      backgroundColor: "#11141b",
      height: "100%",
    },
    ".cm-content": {
      caretColor: "#7cc4ff",
      fontFamily:
        "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace",
      fontSize: "0.82rem",
      lineHeight: "1.45",
    },
    ".cm-gutters": {
      backgroundColor: "#0b0d12",
      color: "#8a93a6",
      border: "none",
    },
    ".cm-activeLine": {
      backgroundColor: "rgba(124,196,255,0.05)",
    },
    ".cm-activeLineGutter": {
      backgroundColor: "rgba(124,196,255,0.08)",
    },
    ".cm-selectionBackground, ::selection": {
      backgroundColor: "#2d4055 !important",
    },
    ".cm-diagnostic": {
      fontSize: "0.72rem",
    },
  },
  { dark: true },
);

function langExtension(lang: EditorLang): Extension {
  switch (lang) {
    case "yaml":
      return yaml();
    case "markdown":
      return markdown();
    case "json":
      return json();
    case "javascript":
      return javascript();
  }
}

export function createEditor(
  parent: HTMLElement,
  opts: CreateEditorOptions,
): { view: EditorView; setDoc: (text: string) => void } {
  const extensions: Extension[] = [
    history(),
    bracketMatching(),
    indentOnInput(),
    highlightActiveLine(),
    foldGutter(),
    darkTheme,
    keymap.of([...defaultKeymap, ...historyKeymap]),
    langExtension(opts.lang),
    EditorView.updateListener.of((upd) => {
      if (upd.docChanged && opts.onChange) {
        opts.onChange(upd.state.doc.toString());
      }
    }),
    EditorView.domEventHandlers({
      blur: (_e: FocusEvent, view: EditorView) => {
        opts.onBlur?.(view.state.doc.toString());
        return false;
      },
    }),
  ];
  if (opts.wrapping !== false) extensions.push(EditorView.lineWrapping);
  if (opts.lint) {
    extensions.push(linter((view) => opts.lint!(view.state.doc.toString())));
    extensions.push(lintGutter());
  }
  // Line numbers are helpful on larger screens; kept on by default.
  extensions.push(lineNumbers());

  const state = EditorState.create({ doc: opts.doc, extensions });
  const view = new EditorView({ state, parent });
  return {
    view,
    setDoc(text: string) {
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: text },
      });
    },
  };
}

export { Compartment };
