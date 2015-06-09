package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import javax.swing.event.*;
import gnue.forms.rpc.RpcException;
import java.util.*;

public class Notebook extends Widget implements ChangeListener {

	/** == component */
	protected JTabbedPane tabbedPane;
	private Map<JComponent, Widget> containers = new WeakHashMap<JComponent, Widget>();

	public Notebook(Desktop desktop, Integer id) {
		super(desktop, id);
		setComponent(tabbedPane = createDefaultTabbedPane());
	}

	public JTabbedPane createDefaultTabbedPane() {
		return new JTabbedPane();
	}

	protected void setComponent(JComponent component) {
		super.setComponent(component);
		((JTabbedPane)component).addChangeListener((ChangeListener)this);
	}

	public void uiAddPage(Widget container, String caption, String tip) {
		containers.put(container.getComponent(), container);
		tabbedPane.addTab(caption, null, container.getComponent(), "".equals(tip) ? null : tip);
		//ystem.out.println(">>>>>> Adding " + container.getComponent() + " , " + container);
	}

	public void uiSelectPage(Widget container) {
		tabbedPane.setSelectedComponent(container.getComponent());
	}

	public void uiSetPageText(Widget container, String caption) {
		int index = findComponent(container.getComponent());
		if (index >= 0) {
			tabbedPane.setTitleAt(index, caption);
		}
		else {
			//ystem.out.println("* Setting title '" + caption + "' to component '" + container + "' not added yet");
		}
	}

	public Widget getPage(Component c) {
		if (c != null) {
			Widget container = containers.get(c);
			if (container == null) {
				throw new RuntimeException("Container not found for component: " + tabbedPane.getSelectedComponent());
			}
			return container;
		}
		else {
			return null;
		}
	}

	public void stateChanged(ChangeEvent event) {
		Widget container = getPage(tabbedPane.getSelectedComponent());
		callAfter("onPageChanged", container);
	}

	public int findComponent(Component component) {
		for (int i=0; i<tabbedPane.getComponentCount(); i++) {
			if (component == tabbedPane.getComponent(i))
				return i;
		}
		return -1;
	}

	public boolean isVerticalGrowable() {
		return true;
	}

}
