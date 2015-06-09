package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import javax.swing.event.*;
import gnue.forms.rpc.RpcException;
import java.util.*;
import gnue.forms.components.*;
import org.json.*;

public class PopupWindow extends FrameAbstract implements PopupControl.PopupListener {

	PopupControl popupControl;
	PopupControl.PopupWindow popupWindow;

	public PopupWindow(Desktop desktop, Integer id, EntryPicker entryPicker) {
		super(desktop, id);
		popupControl = (PopupControl)entryPicker.getComponent();
		popupWindow = popupControl.getPopupWindow();
		JPanel panel = new JPanel(new BorderLayout());
		popupWindow.add(panel);
		setComponent(panel);

		popupControl.addPopupListener(this);

	}

	public PopupWindow(Desktop desktop, Integer id, EntryPicker_with_editor entryPicker) {
		this(desktop, id, (EntryPicker)entryPicker);
	}


	public void uiPopup() {
		popupControl.popup(false);
	}

	public void uiPopdown() {
		popupControl.popdown();
	}

	public void uiSetModal(Boolean modal) {
		// TODO
		popupWindow.setModal(modal);
	}

	public void uiAdd(Widget widget) {
		super.uiAdd(widget);
		popupWindow.validate();
	}

	public void uiSetMenuBar(Widget menuBar) {
		popupWindow.setJMenuBar((JMenuBar)menuBar.getComponent());
	}
	
	public void uiSetTitle(String title) {
		popupWindow.setTitle(title);
	}

	public void uiClose() {
		// TODO: check it out
		popupWindow.setVisible(false);
	}
	
	public void uiDestroy() {
		popupWindow.dispose();
	}

	public void uiShow(Boolean modal) {
		uiShowMessage("PopupWindow has can't uiShow", "error", "error", false, false);
	}
	
	public void uiFit() {
		popupWindow.pack();
	}
	

	/////////////////////////////////////////////////////////
	// PopupListener control popups popupWindow
	// 
	public void popup(PopupControl.PopupEvent event) {
		callAfter("onPopup", event.isPopup());
	}

	//////////////////////////////////////////////////////////////////////////////
	// state
	//
	public JSONObject getState() {
		JSONObject state = new JSONObject();
		state.put("width", popupWindow.getWidth());
		state.put("height", popupWindow.getHeight());
		return state;
	}

	public void setState(JSONObject state) {
		popupWindow.setSize(state.getInt("width"), state.getInt("height"));
	}

}
