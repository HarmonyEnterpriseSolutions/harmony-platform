package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import gnue.forms.rpc.RpcException;
import org.wonderly.swing.tabs.*;

public class NotebookCloseable extends Notebook implements TabCloseListener {

	boolean closable;

	public NotebookCloseable(Desktop desktop, Integer id, Boolean closable) {
		super(desktop, id);
		this.closable = closable;
	}

	public JTabbedPane createDefaultTabbedPane() {
		CloseableTabbedPane ctp = new CloseableTabbedPane();
		ctp.addTabCloseListener(this);
		return ctp;
	}

	/**
	 * server side form already closed, just remove page
	 */
	public void uiRemovePage(Widget container, Boolean exiting) {
		tabbedPane.remove(container.getComponent());
		if (exiting) {
			// continue exit, pass new selected page
			Component selectedComponent = tabbedPane.getSelectedComponent();
			callAfter("onExit", getPage(tabbedPane.getSelectedComponent()));
		}
	}

	public void uiExit() {
		callAfter("onPageClose", getPage(tabbedPane.getSelectedComponent()), /** exiting = **/ true);
	}

	/*
	 * Event: Button pressed to close tab
	 */
	public void tabClosed(final TabCloseEvent event) {
		callAfter("onPageClose", getPage(tabbedPane.getComponentAt(event.getClosedTab())), /** exiting = **/ false);
	}


	public void uiAddPage(Widget container, String caption, String tip) {
		super.uiAddPage(container, caption, tip);
		if (!closable) {
			((CloseableTabbedPane)tabbedPane).setUnclosableTab(tabbedPane.getTabCount()-1);
		}
	}

}
