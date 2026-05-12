// ExportRadanDecompile.java
// Ghidra headless post-script for Radan IPA Symbol Architect.
// Args: <output-directory>

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.Iterator;

import ghidra.app.decompiler.ClangTokenGroup;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class ExportRadanDecompile extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            println("Usage: ExportRadanDecompile.java <output-directory>");
            return;
        }

        File outDir = new File(args[0]);
        outDir.mkdirs();

        File funcsFile = new File(outDir, "functions.tsv");
        File symsFile = new File(outDir, "symbols.tsv");
        File decompDir = new File(outDir, "decompiled");
        decompDir.mkdirs();

        DecompInterface ifc = new DecompInterface();
        DecompileOptions options = new DecompileOptions();
        ifc.setOptions(options);
        ifc.openProgram(currentProgram);

        try (PrintWriter funcs = new PrintWriter(new FileWriter(funcsFile))) {
            funcs.println("entry\tname\tbody_size\tdecompile_file\tstatus");
            Iterator<Function> it = currentProgram.getFunctionManager().getFunctions(true);
            int count = 0;
            while (it.hasNext() && !monitor.isCancelled()) {
                Function fn = it.next();
                count++;
                String addr = fn.getEntryPoint().toString();
                String name = fn.getName();
                String safeName = name.replaceAll("[^A-Za-z0-9_.-]", "_");
                if (safeName.length() > 120) safeName = safeName.substring(0, 120);
                File decompFile = new File(decompDir, addr + "_" + safeName + ".c");
                String status = "ok";
                int size = 0;
                try {
                    DecompileResults res = ifc.decompileFunction(fn, 30, monitor);
                    if (res != null && res.decompileCompleted()) {
                        ClangTokenGroup ccode = res.getCCodeMarkup();
                        String text = ccode != null ? ccode.toString() : "";
                        size = text.length();
                        try (PrintWriter pw = new PrintWriter(new FileWriter(decompFile))) {
                            pw.println("// Function: " + name);
                            pw.println("// Entry: " + addr);
                            pw.println(text);
                        }
                    } else {
                        status = res != null ? res.getErrorMessage() : "decompile returned null";
                    }
                } catch (Throwable t) {
                    status = t.toString();
                }
                funcs.println(addr + "\t" + name + "\t" + size + "\t" + decompFile.getName() + "\t" + status.replace('\t', ' '));
                if (count % 250 == 0) println("Exported/decompiled functions: " + count);
            }
        }

        try (PrintWriter syms = new PrintWriter(new FileWriter(symsFile))) {
            syms.println("address\tname\ttype\tnamespace\tsource");
            SymbolIterator sit = currentProgram.getSymbolTable().getAllSymbols(true);
            while (sit.hasNext() && !monitor.isCancelled()) {
                Symbol s = sit.next();
                syms.println(s.getAddress() + "\t" + s.getName() + "\t" + s.getSymbolType() + "\t" + s.getParentNamespace() + "\t" + s.getSource());
            }
        }

        AddressSetView memory = currentProgram.getMemory();
        try (PrintWriter info = new PrintWriter(new FileWriter(new File(outDir, "program_info.txt")))) {
            info.println("name=" + currentProgram.getName());
            info.println("language=" + currentProgram.getLanguageID());
            info.println("compiler=" + currentProgram.getCompilerSpec().getCompilerSpecID());
            info.println("image_base=" + currentProgram.getImageBase());
            info.println("memory=" + memory);
        }

        ifc.dispose();
        println("Radan decompile export complete: " + outDir.getAbsolutePath());
    }
}
