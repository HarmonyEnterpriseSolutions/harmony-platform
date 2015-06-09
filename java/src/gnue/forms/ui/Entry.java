package gnue.forms.ui;

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;

/**
 * Widget with data exchange
 *	   can be a table editor component
 */

public abstract class Entry extends WidgetNavigable {

	/*
	 * if flag is true, editor not sending navigation events to server
	 */
	protected boolean isInTable = false;
	protected int align;

	public Entry(Desktop desktop, Integer id, String label, String tip, Integer align) {
		super(desktop, id, label, tip);
		this.align = align;
	}
	
	public int getAlign() {
		return align;
	}

	public void setInTable() {
		isInTable = true;
	}


	//-------------------------------------------------------------------------
	// UI INTERFACE

	/**
	* if false, can copy from entry but edit
	*/
	public void uiSetEditable(Boolean editable) {
		getComponent().setEnabled(editable);
	}

	public boolean isEditable() {
		return getComponent().isEnabled();
	}

	public abstract void uiSetText(String value);
	public abstract String getText();
	
	/**
	 * table uses setValue to init entry before editing
	 * table has Booleans for checkboxes and string for other
	 */
	public abstract void setValue(Object value);

	/**
	 * table uses getValue to obtain new editor value
	 */
	public abstract Object getValue();
	
	//-------------------------------------------------------------------------
	// TABLE INTERFACE

	/**
	* value class for Table
	*/
	public Class getColumnClass() {
		return Object.class;
	}

	//-------------------------------------------------------------------------
	// KeyEvent
	//
	protected boolean isNavigationEvent(KeyEvent event) {
		if (isInTable) {
			// if entry receives events as table editor, it must stop editing before
			// and then TODO: send keypressed to server
			return false;
		}
		else {
			switch (event.getKeyCode()) {
				case KeyEvent.VK_ESCAPE:
					return !isInTable;
				case KeyEvent.VK_ENTER:
					return true;
				case KeyEvent.VK_UP:
				case KeyEvent.VK_DOWN:
					return event.isShiftDown() && !event.isAltDown() && !event.isControlDown();
				default:
					return super.isNavigationEvent(event);
			}
		}
	}
}
