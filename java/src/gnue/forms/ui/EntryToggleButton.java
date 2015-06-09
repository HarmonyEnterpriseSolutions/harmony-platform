package gnue.forms.ui;
import javax.swing.*;
import java.awt.event.*;


public abstract class EntryToggleButton extends Entry implements ItemListener {

	/**
	 * Method EntryCheckbox
	 *
	 *
	 */
	public EntryToggleButton(Desktop desktop, Integer id, String tip, Integer align) {
		super(desktop, id, null, tip, align);
	}

	private JToggleButton getToggleButton() {
		return (JToggleButton) getComponent();
	}

	protected void setComponent(JComponent component) {
		super.setComponent(component);
		getToggleButton().addItemListener(this);
	}

	public void itemStateChanged(ItemEvent event) {
		//ystem.out.println(">>> ITEM STATE changed: " + (event.getStateChange() == event.SELECTED));
		SwingUtilities.invokeLater(new Runnable(){
			public void run() {
				call("onChecked", getToggleButton().isSelected());
			}
		});
	}

	public void uiSetText(String value) {
		setValue(!value.equals("0"));
	}
	public String getText() {
		return getToggleButton().isSelected() ? "1" : "0";
	}
	
	public void setValue(Object value) {
		// quiet set selected
		quietSetSelected((Boolean)value);
	}

	public Object getValue() {
		return getToggleButton().isSelected();
	}

	protected void quietSetSelected(boolean selected) {
		getToggleButton().removeItemListener(this);
		try {
			getToggleButton().setSelected(selected);
		}
		finally {
			getToggleButton().addItemListener(this);
		}
	}

	public void setInTable() {
		super.setInTable();
		// hide label when editing table
		getToggleButton().setText("");
		getToggleButton().setHorizontalAlignment(SwingConstants.CENTER);

	}

	public Class getColumnClass() {
		return Boolean.class;
	}

}

