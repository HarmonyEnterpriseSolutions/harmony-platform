package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import org.json.*;

import gnue.forms.components.JStatusBar;

public class StatusBar extends Widget {

	private JStatusBar statusBar;

	public StatusBar(Desktop desktop, Integer id, JSONArray columnWidths) {
		super(desktop, id);

		int[] widths = (int[])JSONUtils.jsonArrayToObjectArray(columnWidths, int.class);

		statusBar = new JStatusBar(widths);
		setComponent(statusBar);
	}

	public void uiSetStatusText(String text, Integer pos) {
		statusBar.setStatusText(text, pos);
	}

}
