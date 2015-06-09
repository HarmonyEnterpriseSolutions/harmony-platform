package gnue.forms.components;

import java.awt.*;
import javax.swing.*;
import javax.swing.event.*;


public class JListTabs extends JTabbedPane implements SingleSelectionListComponent {

    private ListModel model = null;
    private Component component = null;
	private ListDataListener dataListener = new ListDataListener() {

		public void contentsChanged(ListDataEvent e) {
			for (int i=e.getIndex0(); i<=e.getIndex1(); i++) {
				setTitleAt(i, model.getElementAt(i).toString());
			}
		}
	
		public void intervalAdded(ListDataEvent e) {
			if (e.getIndex0() == getTabCount()) {
				for (int i=e.getIndex0(); i<=e.getIndex1(); i++) {
					addTab(model.getElementAt(i).toString(), createPanel());
				}
			}
			else {
				for (int i=e.getIndex1(); i>=e.getIndex0(); i--) {
					insertTab(model.getElementAt(i).toString(), null, createPanel(), null, 0);
				}
			}
		}
	
		public void intervalRemoved(ListDataEvent e) {
			for (int i=e.getIndex1(); i>e.getIndex0()-1; i--) {
				removeTabAt(i);
			}
		}
    };

	public JListTabs(ListModel model) {
		super();
		setListModel(model);
		addChangeListener(new ChangeListener(){
			public void stateChanged(ChangeEvent e)  {
				JPanel panel = (JPanel)getSelectedComponent();
				if (panel!= null && component != null) {
					panel.add(component);
				}
			}
		});
	}
	
	public Component add(Component component) {
		this.component = component;
		JPanel panel = (JPanel)getSelectedComponent();
		if (panel != null) {
			panel.add(component);
		}
		return component;
	}

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
    
    public SingleSelectionModel getSelectionModel() {
    	return getModel();
    }
    
	private JPanel createPanel() {
		return new JPanel(new BorderLayout());
	}

    /**
     * Create the GUI and show it.  For thread safety,
     * this method should be invoked from
     * the event dispatch thread.
     */
    private static void createAndShowGUI() {
        //Create and set up the window.
        JFrame frame = new JFrame("TabbedPaneDemo");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        
        DefaultListModel m = new DefaultListModel();
        JComponent c = new JListTabs(m);
        m.addElement("Hello");
        m.addElement("World");

        c.add(new JButton("Component"));


        //Add content to the window.
        frame.add(c, BorderLayout.CENTER);
        
        //Display the window.
        frame.pack();
        frame.setVisible(true);
    }
    
    public static void main(String[] args) {
        //Schedule a job for the event dispatch thread:
        //creating and showing this application's GUI.
        SwingUtilities.invokeLater(new Runnable() {
            public void run() {
                //Turn off metal's use of bold fonts
				createAndShowGUI();
            }
        });
    }
    
}