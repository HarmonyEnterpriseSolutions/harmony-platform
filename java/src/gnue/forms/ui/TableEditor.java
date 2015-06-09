package gnue.forms.ui;

import javax.swing.*;
import javax.swing.event.*;
import javax.swing.table.*;
import java.awt.event.*;
import org.json.*;
import java.util.*;
import java.beans.*;
//import javax.swing.text.JTextComponent;
//import gnue.forms.components.PopupControl;


class TableEditor extends AbstractCellEditor implements TableCellEditor {

	private Entry entry;
	private Table table;

	public TableEditor(Table table, Entry anEntry) {
		this.table = table;
		this.entry = anEntry;
		entry.setInTable();
		
		addCellEditorListener(new CellEditorListener() {
			public void editingStopped(ChangeEvent e) {
				System.out.println("EDITING STOPPED");
				if (entry instanceof EntryPicker) {
					((EntryPicker)entry).popdown();
				}
				entry.call("onStopCellEditing", entry.getText());
			}
			public void editingCanceled(ChangeEvent e) {
				System.out.println("EDITING CANCELED");
				if (entry instanceof EntryPicker) {
					((EntryPicker)entry).popdown();
				}
			}
		});
	}

	public java.awt.Component getTableCellEditorComponent(JTable table, Object value, boolean isSelected, int row, int column) {
		//stem.out.println("TableEditor: getTableCellEditorComponent, " + value);

		entry.setValue(value);
		
		// select text before editing
		if (entry instanceof EntryAbstractText) {
			((EntryAbstractText)entry).getTextComponent().selectAll();
		}
		
		entry.getFocusComponent().requestFocus();
		return entry.getComponent();
	}

	public Object getCellEditorValue() {
		return entry.getValue();
	}

	public boolean isCellEditable(EventObject event) {
		if (event instanceof MouseEvent) {
			return ((MouseEvent)event).getClickCount() >= 2;
		} else {
			return super.isCellEditable(event);
		}
	}

	//public boolean stopCellEditing() {
	//	//stem.out.println("TableEditor: stopCellEditing");
	//	return super.stopCellEditing();
	//}

	// cancelCellEditing never called, only if stopCellEditing returns false
	
	/**
	 * Returns true if the editing cell should be selected, false otherwise.
	 */
	public boolean shouldSelectCell(EventObject anEvent) {
		return true;
	}
	
	//public void improveFocus() {
	//	if (entry.getFocusComponent() != entry.getComponent()) {
	//		SwingUtilities.invokeLater(new Runnable(){
	//			public void run() {
	//				entry.getFocusComponent().requestFocus();
	//			}
	//		});
	//	}
	//}

}
