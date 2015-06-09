package org.wonderly.swing.tabs;

import javax.swing.plaf.basic.BasicTabbedPaneUI;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import org.wonderly.awt.*;
import java.util.logging.*;
import java.util.*;

/**
<pre>
Copyright (c) 1997-2006, Gregg Wonderly
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above
      copyright notice, this list of conditions and the following
      disclaimer in the documentation and/or other materials provided
      with the distribution.
    * The name of the author may not be used to endorse or promote
      products derived from this software without specific prior
      written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.
</pre>
 *
 *  This class is a subclass of JTabbedPane which provides tab close buttons.
 */
public class CloseableTabbedPane extends JTabbedPane {
	private Logger log = Logger.getLogger( getClass().getName() );
	private Vector<TabCloseListener> tlis = new Vector<TabCloseListener>();
	Vector<Integer>unclosable = new Vector<Integer>();
	private volatile BasicTabbedPaneUI ui;

	/**
	 *  Tyically, the last tab open is not closable.  So, call this method with a
	 *  tab number and that tab will not contain a close icon.  If you monitor
	 *  with a {@link TabCloseListener}, you can use {@link #getTabCount()} and
	 *  when it is 1, you can call {@link #setUncloseableTab(int)}(0) to make the
	 *  last tab unclosable.
	 *  @see #setCloseableTab(int);
	 */
	public void setUnclosableTab( int val ) {
		if( unclosable.contains(val) )
			return;
		unclosable.addElement(val);
	}
	/**
	 *  Use this method to reverse the actions of {@link #setUnclosableTab(int)}
	 */
	public void setClosableTab( int val ) {
		unclosable.removeElement( val );
	}
	/** Add a tab close listener. On close events, the listener is responsible
	 *  for deleting the tab or otherwise reacting to the event.
	 */
	public void addTabCloseListener( TabCloseListener lis ) {
		tlis.addElement( lis );
	}
	/** Remove a tab close listener */
	public void removeTabCloseListener( TabCloseListener lis ) {
		tlis.removeElement( lis );
	}

	/** Create a new tabbed pane */
	public CloseableTabbedPane( ) {
		this( JTabbedPane.TOP );
	}

	/** Create a tabbed pane */
	public CloseableTabbedPane( int placement ) {
		this( placement, JTabbedPane.WRAP_TAB_LAYOUT );
	}

	/** Create a tabbed pane */
	public CloseableTabbedPane( int placement, int layout ) {
		super( placement, layout );
		
		if ("Windows".equals(UIManager.getLookAndFeel().getID())) {
			ui = new WindowsClosableTabbedPaneUI(this);
		}
		else {
			ui = new MetalClosableTabbedPaneUI(this);
		}
		
		setUI( ui );
		ImageIcon ic = new ImageIcon( getClass().getClassLoader().getResource("org/wonderly/swing/tabs/close.jpg") );
		ImageIcon dc = new ImageIcon( getClass().getClassLoader().getResource("org/wonderly/swing/tabs/down.jpg") );
		setCloseIcons(ic,dc);
	}
	
	public void setCloseIcons( ImageIcon ic, ImageIcon downIcon ) {
		((ClosableTabbedPaneUI)ui).setCloseIcons( ic, downIcon );
	}

	/**
         *  A text/example main that will show you how this works.
	 */
	public static void main( String args[] ) {
		JFrame f = new JFrame( "Testing");
		Packer pk = new Packer( f.getContentPane() );
		final CloseableTabbedPane tp = new CloseableTabbedPane();

		final int cnt[] = {0};
		pk.pack( tp ).fillboth().gridx(0).gridy(0).gridh(2);
		final JButton add = new JButton("Add New Tab");
		pk.pack( add ).gridx(1).gridy(0).inset(4,4,4,4);
		pk.pack( new JPanel() ).gridx(1).gridy(1).filly();
		add.addActionListener( new ActionListener() {
			public void actionPerformed( ActionEvent ev ) {
				if( tp.getTabCount() >= 1 )
					tp.setClosableTab(0);
				tp.add( "Tab-"+cnt[0]++, new JPanel() );
			}
		});

		for( int i = 0; i < 5; ++i ) {
			tp.add( "Tab-"+i, new JPanel());
			++cnt[0];
		}
		f.pack();
		f.setSize( 700, 500 );
		f.addWindowListener( new WindowAdapter() {
			public void windowClosing( WindowEvent ev ) {
				System.exit(1);
			}
		});
		tp.addTabCloseListener( new TabCloseListener() {
			public void tabClosed( TabCloseEvent ev ) {
				int tab = ev.getClosedTab();
				tp.removeTabAt( tab );
				if( tp.getTabCount() == 1 )
					tp.setUnclosableTab(0);
			}
		});
		f.setLocationRelativeTo( null );
		f.setVisible(true);
	}
	
	void closeTab( int tab ) {
		log.fine("Closing tab: "+tab+", listeners: "+tlis );
		if( tlis.size() == 0 )
			return;
		TabCloseEvent ev = new TabCloseEvent( this, tab );
		for( TabCloseListener l: tlis ) {
			try {
				log.finer("Sending close to: "+l );
				l.tabClosed( ev );
			} catch( Exception ex ) {
				log.log( Level.SEVERE, ex.toString(), ex );
			}
		}
	}
	
	public void setCloseSize( int sz ) {
		((ClosableTabbedPaneUI)ui).setCloseWidth(sz);
		repaint();
	}	

}
