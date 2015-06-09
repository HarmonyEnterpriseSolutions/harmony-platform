package gnue.forms.ui;
import javax.swing.*;

public class URLViewerStub extends URLViewer {
	private JTextArea textArea;
	public URLViewerStub(Desktop desktop, Integer id, String label) {
		super(desktop, id, label);
		textArea = new JTextArea();
		textArea.setEditable(false);
		setComponent(textArea);
	}

	public void uiSetUrl(String url) {
		textArea.setText("Content not supported:\n" + url);
	}
}
