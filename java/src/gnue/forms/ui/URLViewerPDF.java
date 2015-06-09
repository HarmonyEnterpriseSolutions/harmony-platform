package gnue.forms.ui;
import gnue.forms.components.PDFViewer;
import java.net.*;
import java.io.*;
import java.util.*;

public class URLViewerPDF extends URLViewer {
	public URLViewerPDF(Desktop desktop, Integer id, String label) {
		super(desktop, id, label);
		setComponent(new PDFViewer(false));
	}

	public void uiSetUrl(String url) {
		PDFViewer viewer = (PDFViewer) getComponent();
		if (url.length() > 0) {
			try {
				viewer.openFile(getDesktop().wrapUrl(url));
			}
			catch (IOException e) {
				e.printStackTrace();
				getDesktop().printStackTrace(e, "Error on report server");
			}
		}
		else {
			viewer.doClose();
		}
	}
}
