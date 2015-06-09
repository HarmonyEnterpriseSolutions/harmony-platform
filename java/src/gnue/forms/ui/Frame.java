package gnue.forms.ui;

import javax.swing.*;
import javax.swing.event.*;
import java.awt.*;
import java.awt.event.*;
import org.json.*;
import java.util.*;
import java.net.*;
import gnue.forms.components.FrameComponent;

public class Frame extends FrameAbstract {


	/** == component */
	protected FrameComponent frame;
	boolean fit = false;
	
	/**  delayed state bounds */
	private Rectangle bounds = null;


	public Frame(Desktop desktop, Integer id, String title, JSONArray windowStyle) {
		super(desktop, id, windowStyle);

		frame = desktop.getDesktopComponent().createFrameComponent(title, resizable, closable, maximizable, iconifiable, new Runnable() {
			public void run() {
				callAfter("onClose");
			}
		});

		setComponent(frame.asComponent());
	}

	public void uiFit() {
		// deferred until uiShow
		fit = true;
	}

	public void uiShow(Boolean modal) {
		frame.show(modal, this.maximize, this.fit, this.bounds);
		this.bounds = null;
	}

	public void uiClose() {
		frame.doHide();
	}

	public void uiDestroy() {
		frame.dispose();
	}

	public void uiSetTitle(String title) {
		frame.setTitle(title);
	}

	public void uiSetMenuBar(Widget menuBar) {
		frame.setJMenuBar((JMenuBar)menuBar.getComponent());
	}

	//////////////////////////////////////////////////////////////////////////////
	// state
	//
	public JSONObject getState() {
		Rectangle rect = this.bounds != null ? this.bounds : frame.getBounds();
		JSONObject state = new JSONObject();
		state.put("x", rect.x);
		state.put("y", rect.y);
		state.put("width",  rect.width);
		state.put("height", rect.height);
		return state;
	}

	public void setState(JSONObject state) {
		// have to delay this till uiShow
		this.bounds = new Rectangle(
			state.getInt("x"), 
			state.getInt("y"), 
			state.getInt("width"), 
			state.getInt("height")
		);
	}

}

