package gnue.forms.ui;

import javax.swing.*;
import javax.swing.text.*;
import java.awt.*;
import java.awt.event.*;
import org.json.*;
import gnue.forms.rpc.RpcException;

/**
 * JTextComponent based entries
 */
public abstract class EntryAbstractText extends Entry {

	private String oldText = null;

	public EntryAbstractText(Desktop desktop, Integer id, String label, String tip, Integer align) {
		super(desktop, id, label, tip, align);

	}

	//-------------------------------------------------------------------------

	protected void setComponent(JComponent component) {
		super.setComponent(component);

		JComponent c = getComponent();
		// text component preferred size width calculated as text size
		// make it static
		Dimension d = c.getPreferredSize();
		//ystem.out.println("PREF SIZE: " + d);
		d.width = 100;
		c.setPreferredSize(d);

		// text c minimum size is wery small
		// make it static
		d = c.getMinimumSize();
		//ystem.out.println("PREF SIZE: " + d);
		if (d.width < 100) {
			d.width = 100;
			c.setMinimumSize(d);
		}
		
		if (getTextComponent() instanceof JTextField) {
			int halign;
			switch ((getAlign() - 1) % 3) {
				case 1:  halign = JTextField.CENTER; break;
				case 2:  halign = JTextField.RIGHT; break;
				default: halign = JTextField.LEFT; break;
			}
			((JTextField)getTextComponent()).setHorizontalAlignment(halign);
		} 
		
	}
	
	/**
	 * getTextComponent() property, equals to component by default
	 */
	public JTextComponent getTextComponent() {
		return (JTextComponent)getComponent();
	}

	public JComponent getFocusComponent() {
		return getTextComponent();
	}

	protected boolean onKeyPressed(KeyEvent event) {
		boolean navigation = super.onKeyPressed(event);
		if (!navigation) {
			maybeTextChanged();
		}
		return navigation;
	}
	
	protected void maybeTextChanged() {
		// prevented text change notification in case of VK_TAB button
		// this works but not right
		String text = getTextComponent().getText();
		if (!text.equals(oldText)) {
			//System.out.printf("TEXT CHANGED: oldText=%s, text=%s\n", oldText, text);
			oldText = text;
			appendCall("onTextChanged", text, getTextComponent().getCaretPosition());
		}
	}

	//-------------------------------------------------------------------------
	// UI INTERFACE

	/** abstract Entry method implementation */
	public void uiSetEditable(Boolean editable) {
		getTextComponent().setEditable(editable);
	}

	public boolean isEditable() {
		return getTextComponent().isEditable();
	}

	/** abstract Entry method implementation */
	public void uiSetText(String value) {
		oldText = value;
		getTextComponent().setText(value);
	}
	public String getText() {
		return getTextComponent().getText();
	}
	
	public void setValue(Object value) {
		uiSetText((String)value);
	}

	/** abstract Entry method implementation */
	public Object getValue() {
		return getTextComponent().getText();
	}


	public void uiSetSelectedArea(Integer selection1, Integer selection2) {
		getTextComponent().setCaretPosition(selection1);
		getTextComponent().setSelectionStart(selection1);
		getTextComponent().setSelectionEnd(selection2);
	}

	//-------------------------------------------------------------------------

}
