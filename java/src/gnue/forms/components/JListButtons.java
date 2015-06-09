package gnue.forms.components;

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import javax.swing.event.*;


public class JListButtons extends JPanel implements SingleSelectionListComponent {
	
	private ListModel model;
	private SingleSelectionModel selectionModel = null;;
	private GridBagConstraints cs_first = new GridBagConstraints();
	private GridBagConstraints cs;
	
	////////////////////////////////////////////////////////////////////////

	private ListDataListener dataListener = new ListDataListener() {

		public void contentsChanged(ListDataEvent e) {
			for (int i=e.getIndex0(); i<=e.getIndex1(); i++) {
				getButton(i).setText(model.getElementAt(i).toString());
			}
		}
	
		public void intervalAdded(ListDataEvent e) {
			if (e.getIndex0() == getComponentCount()) {
				for (int i=e.getIndex0(); i<=e.getIndex1(); i++) {
					add(createButton(model.getElementAt(i)), getComponentCount() == 0 ? cs_first : cs);
				}
			}
			else {
				throw new RuntimeException("Not implemented");
				//for (int i=e.getIndex1(); i>=e.getIndex0(); i--) {
				//	add(new JButton(model.getElementAt(i).toString()), i);
				//}
			}
		}
	
		public void intervalRemoved(ListDataEvent e) {
			for (int i=e.getIndex1(); i>e.getIndex0()-1; i--) {
				remove(i);
			}
		}
    };

	private ChangeListener selectionListener = new ChangeListener() {
		public void stateChanged(ChangeEvent event) {
			getComponent(selectionModel.getSelectedIndex()).requestFocus();
		}
	};

	private FocusListener focusListener = new FocusAdapter(){
		public void focusGained(FocusEvent e) {
			System.out.println("FOCUS?");
			for (int i=0; i<getComponentCount(); i++) {
				if (getComponent(i) == e.getSource()) {
					System.out.println("FOCUS ON " + i);
					selectionModel.setSelectedIndex(i);
				}
			}
		}
	};

	////////////////////////////////////////////////////////////////////////

	public JListButtons(ListModel model) {
		this(model, new DefaultSingleSelectionModel());
	}

	public JListButtons(ListModel model, SingleSelectionModel selectionModel) {
		super(new GridBagLayout());
		this.setListModel(model);
		this.setSelectionModel(selectionModel);
		
		cs_first.gridx = 0;
		cs_first.weightx = 1.0;
		cs_first.fill = GridBagConstraints.BOTH;
		
		cs = (GridBagConstraints)cs_first.clone();
		
		this.setBackground(Color.DARK_GRAY);
	}
	
	////////////////////////////////////////////////////////////////////////
	
	private JButton getButton(int i) {
		return (JButton) getComponent(i);
	}

	private JButton createButton(Object item) {
		JButton button = new JButton(item.toString());
		button.addFocusListener(focusListener);
		return button;
	}

	////////////////////////////////////////////////////////////////////////

    public void setListModel(ListModel model) {
    	if (this.model != null) {
    		this.model.removeListDataListener(dataListener);
    	}
    	this.model = model;
    	if (this.model != null) {
    		this.model.addListDataListener(dataListener);
    	}
    }
    
    public ListModel getListModel() {
    	return model;
    }
    
    public void setSelectionModel(SingleSelectionModel selectionModel) {
    	if (this.selectionModel != null) {
    		this.selectionModel.removeChangeListener(selectionListener);
    	}
    	this.selectionModel = selectionModel;
    	if (this.selectionModel != null) {
    		this.selectionModel.addChangeListener(selectionListener);
    	}
    }
    public SingleSelectionModel getSelectionModel() {
    	return selectionModel;
    }
    
    public void setInset(int inset) {
    	cs.insets.top = inset;
    }
    
    public int getInset() {
    	return cs.insets.top;
    }
	
}
