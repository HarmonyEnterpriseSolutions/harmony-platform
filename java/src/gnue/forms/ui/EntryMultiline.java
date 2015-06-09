package gnue.forms.ui;

import javax.swing.*;
import javax.swing.text.*;
import java.awt.*;
import java.awt.event.*;
import javax.swing.border.BevelBorder;

public class EntryMultiline extends EntryAbstractText {

	private JTextArea textArea;

	public EntryMultiline(Desktop desktop, Integer id, String label, String tip, Integer align) {
		super(desktop, id, label, tip, align);
		textArea = new JTextArea();
		setComponent(new JScrollPane(textArea));
	}
	
	public JTextComponent getTextComponent() {
		return textArea;
	}

	public boolean isVerticalGrowable() {
		return true;
	}

	protected boolean isNavigationEvent(KeyEvent event) {
		switch (event.getKeyCode()) {
			case KeyEvent.VK_ENTER:
			case KeyEvent.VK_UP:
			case KeyEvent.VK_DOWN:
				return false;
			default:
				return super.isNavigationEvent(event);
		}
	}

}
