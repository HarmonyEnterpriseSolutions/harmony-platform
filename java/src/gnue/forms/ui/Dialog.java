package gnue.forms.ui;

import javax.swing.*;
import javax.swing.event.*;
import java.awt.*;
import java.awt.event.*;
import org.json.*;
import java.util.*;
import java.net.*;
import gnue.forms.components.Utils;

public class Dialog extends FrameAbstract {

	/**
	 * Dialog with isDisposed method
	 */
	static class DialogComponent extends JDialog {
		private boolean disposed = false;
		
		public DialogComponent(java.awt.Frame frame, String title) {
			super(frame, title);
		}
		
		public void dispose() {
			disposed = true;
			super.dispose();
		}

		public boolean isDisposed() {
			return disposed;
		}
		
	}

	/** == component */
	protected DialogComponent dialog;

	public Dialog(Desktop desktop, Integer id, String title, JSONArray windowStyle) {
		super(desktop, id, windowStyle);

		dialog = new DialogComponent(Utils.getTopLevelFrame(getDesktop().getComponent()), title);

		setComponent((JComponent)dialog.getContentPane());

		//if (maximize) {
		//}

		dialog.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE);
		dialog.addWindowListener(new WindowAdapter() {
			public void windowClosing(WindowEvent evt) {
				callAfter("onClose");
			}
		});

	}

	public void uiFit() {
		dialog.pack();
		centerOnParent();
	}
	
	protected void centerOnParent() {
		// center on parent
		Dimension size = dialog.getSize();
		
		Dimension psize;
		Point pos;
		try {
			psize = dialog.getParent().getSize();
			pos = dialog.getParent().getLocationOnScreen();
		}
		catch (java.awt.IllegalComponentStateException e) {
			psize = java.awt.Toolkit.getDefaultToolkit().getScreenSize();
			pos = new Point(0,0);
		}
		
		dialog.setLocation(pos.x + (psize.width - size.width) / 2, pos.y+(psize.height - size.height) / 2);
	}

	public void uiShow(Boolean modal) {
		dialog.setModal(modal);
		dialog.setVisible(true);
		if (modal && !dialog.isDisposed()) {
			callAfter("onAfterModal");
		}
	}

	public void uiClose() {
		dialog.setVisible(false);
		dialog.setModal(false);
	}

	public void uiDestroy() {
		dialog.dispose();
	}

	public void uiSetTitle(String title) {
		dialog.setTitle(title);
	}

	public void uiSetMenuBar(Widget menuBar) {
		dialog.setJMenuBar((JMenuBar)menuBar.getComponent());
	}

	//////////////////////////////////////////////////////////////////////////////
	// state
	//
	public JSONObject getState() {
		JSONObject state = new JSONObject();
		state.put("width", dialog.getWidth());
		state.put("height", dialog.getHeight());
		return state;
	}

	public void setState(JSONObject state) {
		dialog.setSize(state.getInt("width"), state.getInt("height"));
		centerOnParent();
	}
}

