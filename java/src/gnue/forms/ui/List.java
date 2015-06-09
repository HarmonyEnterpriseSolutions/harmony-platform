package gnue.forms.ui;

import gnue.forms.components.*;
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import javax.swing.event.*;
import org.json.*;


public class List extends WidgetNavigable implements ChangeListener {

	JSONArrayListModel model = new JSONArrayListModel();
	SingleSelectionModel selectionModel;
	boolean fireSelectionEvents = true;
	
	public List(Desktop desktop, Integer id, String label, String style) {
		super(desktop, id, label);
		
		try {
			Class listClass = Class.forName("gnue.forms.components.JList" + style.substring(0,1).toUpperCase() + style.substring(1));
			setComponent((JComponent)listClass.getConstructor(new Class[]{ListModel.class}).newInstance(new Object[]{model}));
		} 
		catch(Exception e) {
			throw new RuntimeException(e);
		}
		
		if (getComponent() instanceof JListButtons) {
			((JListButtons)getComponent()).setInset(Box.INSETY);
		}
		
		selectionModel = ((SingleSelectionListComponent)getComponent()).getSelectionModel();
		selectionModel.addChangeListener(this);
	}
	
	public void uiSetValues(JSONArray values) {
		fireSelectionEvents = false;
		model.setData(values);
		fireSelectionEvents = true;
	}

	public void uiSetValue(Integer index, String value) {
		model.setElementAt(value, index);
	}
	
	public void uiSelectRow(Integer index) {
		fireSelectionEvents = false;
		selectionModel.setSelectedIndex(index);
		fireSelectionEvents = true;
	}
	
	public void uiAdd(Widget widget) {
		getComponent().add(widget.getComponent());
	}
	
	public void stateChanged(ChangeEvent event) {
		if (fireSelectionEvents) {
			callAfter("onSelectionChanged", new Integer(selectionModel.getSelectedIndex()));
		}
	}
	
	
	/**
	 * invoked by WidgetNavigable.keyListener
	 * registered to component in WidgetNavigable.setComponent
	 * use appendCall instead call (appended calls will be flushed)
	 */
	protected boolean onKeyPressed(KeyEvent event) {
		boolean navigation = super.onKeyPressed(event);
		if (navigation) {
			if (event.getKeyCode() == KeyEvent.VK_TAB) {
				if (event.isShiftDown()) {
					if (selectionModel.getSelectedIndex() != 0) {
						navigation = false;
					}
				}
				else {
					if (selectionModel.getSelectedIndex() != model.getSize() - 1) {
						navigation = false;
					}
				}
			}
		}
		else {
			if (event.getKeyCode() == KeyEvent.VK_ENTER) {
				appendCall("onNodeActivated");
			}
		}
		return navigation;
	}

	static class JSONArrayListModel extends AbstractListModel {
		JSONArray data = new JSONArray();
		public Object getElementAt(int index) {
			return data.get(index);
		}
		public int getSize() {
			return data.length();
		}
		public void setData(JSONArray data) {
			int oldSize = this.data.length();
			int newSize = data.length();
			this.data = data;
			if (oldSize > newSize) {
			    fireIntervalRemoved(this, newSize, oldSize-1);
			}
			else if (oldSize < newSize) {
			    fireIntervalAdded(this, oldSize, newSize-1);
			}
		}
	    public void setElementAt(Object object, int index) {
			data.put(index, object);
			fireContentsChanged(this, index, index);
	    }
	};

}
