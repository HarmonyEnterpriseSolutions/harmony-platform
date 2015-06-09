package gnue.forms.components;

/**
 * @(#)PopupControl.java
 *
 *
 * @author
 * @version 1.00 2009/7/2
 */

import java.util.*;
import javax.swing.*;
import javax.swing.text.JTextComponent;
import javax.swing.event.*;
import java.awt.*;
import java.awt.event.*;
//import javax.swing.plaf.basic.BasicArrowButton;

public class PopupControl extends TextFieldWithButtons {

	private PopupWindow popupWindow = null;
	private java.util.List<PopupListener> popupListeners = null;

	public PopupControl() {
		super();
		getTextComponent().addKeyListener(new TextComponentKeyListener());
		addButton("...").addActionListener(new ActionListener(){
			public void actionPerformed(ActionEvent event) {
				getTextComponent().requestFocus();
				SwingUtilities.invokeLater(new Runnable(){
					public void run() {
						popup(true);
					}
				});
			}
		});
	}
	
	public PopupWindow getPopupWindow() {
		if (popupWindow == null) {
			popupWindow = new PopupWindow(Utils.getTopLevelFrame(this));

			popupWindow.addWindowFocusListener(new WindowFocusListener(){
				public void windowGainedFocus(WindowEvent e) {
					//System.out.println("************** WINDOW FOCUS GAINED");
				}
				public void windowLostFocus(WindowEvent e) {
					System.out.println("************** WINDOW FOCUS LOST: " + e.getOppositeWindow());
					popdown();

					System.out.println(">>> returning focus to applet");		
					Container c = PopupControl.this.getParent();
					while (c != null) {
						if (c instanceof JApplet) {
							((JApplet)c).requestFocus();
							PopupControl.this.getTextComponent().requestFocus();
							break;
						}
						c = c.getParent();
					}
				}
			});

			//popupWindow.addFocusListener(new FocusListener(){
			//	public void focusGained(FocusEvent e) {
			//		System.out.println("************** FOCUS GAINED");
			//	}
			//	public void focusLost(FocusEvent e) {
			//		System.out.println("************** FOCUS LOST");
			//	}
			//});
			//popupWindow.addKeyListener(new PopupWindowKeyListener());

		}
		return popupWindow;
	}

	public void popup(boolean forceFocus) {
		//Get current screen size
		//Dimension screenSize = Toolkit.getDefaultToolkit().getScreenSize();

		Point pos = getLocationOnScreen();
		pos.y += getHeight();

		getPopupWindow().setLocation(pos);

		//getPopupWindow().setVisible(false);
		getPopupWindow().setFocusableWindowState(forceFocus);
		System.out.println(">>> Focusable: " + forceFocus);
		getPopupWindow().setVisible(true);

		getPopupWindow().setFocusableWindowState(true);

		firePopup(true);
	}

	public void popdown() {
		getPopupWindow().setVisible(false);
		firePopup(false);
	}

	public void addPopupListener(PopupListener l) {
		if (popupListeners == null)
			popupListeners = new ArrayList<PopupListener>();
		popupListeners.add(l);
	}

	public void removePopupListener(PopupListener l) {
		if (popupListeners != null)
			popupListeners.remove(l);
	}

	protected void firePopup(boolean popup) {
		for (PopupListener l: popupListeners) {
			l.popup(new PopupEvent(this, popup));
		}
	}

	public class PopupWindow extends JDialog {
		public PopupWindow(Frame parent) {
			super(parent);
			setLayout(new BorderLayout());
			//setFocusable(false);
			setAlwaysOnTop(true);
			setSize(400, 200);
		}

		protected JRootPane createRootPane() {
			JRootPane rootPane = super.createRootPane();
			KeyStroke stroke = KeyStroke.getKeyStroke("ESCAPE");
			//rootPane.getInputMap(JComponent.WHEN_IN_FOCUSED_WINDOW).put(stroke, "ESCAPE");
			rootPane.getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT ).put(stroke, "ESCAPE");
			rootPane.getActionMap().put("ESCAPE", new AbstractAction() {
				public void actionPerformed(ActionEvent actionEvent) {
					popdown();
				}
			});
			return rootPane;
		}
		
	}


	private class TextComponentKeyListener extends KeyAdapter {
		public void keyPressed(KeyEvent e) {
			if (e.getKeyCode() == KeyEvent.VK_DOWN) {
				popup(true);
			}
		}
	}

	public static class PopupEvent extends AWTEvent {
		public static final int POPUP   = RESERVED_ID_MAX + 1;
		public static final int POPDOWN = RESERVED_ID_MAX + 2;
		PopupEvent(PopupControl source, boolean popup) {
			super(source, popup ? POPUP : POPDOWN);
		}
		public boolean isPopup() {
			return this.getID() == POPUP;
		}
	}

	public interface PopupListener extends EventListener {
		public void popup(PopupEvent evt);
	}

	///////////////////////////////////////////////////////////////////////////
	// TEST

	public static void main(String args[]) {

		final JFrame frame = new JFrame("PopupControl");
		PopupControl pc = new PopupControl();
		pc.addPopupListener(new PopupListener() {
			public void popup(PopupEvent evt) {
				System.out.println("POPUP: " + evt.isPopup());
			}
		});
		
		pc.addButton(">");
		frame.add(pc);
		//frame.add(new JTextField());
		frame.pack();
		frame.setVisible(true);

		frame.addWindowListener(new WindowAdapter() {
			public void windowClosing(WindowEvent evt) {
				frame.dispose();
				System.exit(0);
			}
		});

	}


}
